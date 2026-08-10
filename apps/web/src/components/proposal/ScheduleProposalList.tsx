"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import type { ScheduleProposal } from "@/lib/types/domain";
import { apiClient } from "@/lib/api/client";

interface ProposalCardProps {
  proposal: ScheduleProposal;
  onApprove: (id: string) => Promise<void>;
  onReject: (id: string) => Promise<void>;
}

function ProposalCard({ proposal, onApprove, onReject }: ProposalCardProps) {
  const t = useTranslations("proposal");
  const [confirming, setConfirming] = useState<"approve" | "reject" | null>(null);
  const [loading, setLoading] = useState(false);

  const confidencePct = Math.round(proposal.confidence * 100);

  return (
    <div className="bg-neutral-900 border border-blue-800 rounded-lg p-5 space-y-4">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <span className="text-xs font-mono text-blue-400 uppercase tracking-wider">
            {t("pending")}
          </span>
          <p className="text-white font-medium mt-1">{proposal.why}</p>
        </div>
        <div className="text-right shrink-0">
          <div className="text-green-400 font-mono font-bold text-lg">
            +{proposal.expectedBenefitMinutes} min
          </div>
          <div className="text-neutral-500 text-xs">{t("expectedBenefit")}</div>
        </div>
      </div>

      {/* FACT/INFERENCE/RECOMMENDATION label */}
      <div className="flex items-center gap-2">
        <span className="alert-type-recommendation text-xs px-2 py-0.5 rounded font-mono">
          {proposal.category}
        </span>
        <span className="text-neutral-500 text-xs">
          {t("confidence")}: {confidencePct}%
        </span>
        <span className="text-neutral-500 text-xs">
          {t("affectedScenes")}: {proposal.affectedScenes.join(", ")}
        </span>
      </div>

      {/* Evidence */}
      {proposal.evidence.length > 0 && (
        <div className="bg-neutral-800 rounded p-3 space-y-1">
          <div className="text-neutral-400 text-xs font-semibold uppercase tracking-wider mb-2">
            {t("evidence")}
          </div>
          {proposal.evidence.map((e) => (
            <div key={e.evidenceId} className="text-neutral-300 text-sm">
              {e.description}
            </div>
          ))}
        </div>
      )}

      {/* Risks */}
      {proposal.risks.length > 0 && (
        <div className="space-y-1">
          <div className="text-neutral-400 text-xs font-semibold uppercase tracking-wider">
            {t("risks")}
          </div>
          {proposal.risks.map((r, i) => (
            <div
              key={i}
              className={`text-xs px-2 py-1 rounded severity-${r.severity.toLowerCase()}`}
            >
              {r.description}
            </div>
          ))}
        </div>
      )}

      {/* Action buttons */}
      {proposal.status === "PENDING" && (
        <div className="flex gap-3 pt-2">
          {confirming === "approve" ? (
            <div className="flex items-center gap-3">
              <span className="text-yellow-300 text-sm">{t("approveConfirm")}</span>
              <button
                className="btn-primary text-sm"
                onClick={async () => {
                  setLoading(true);
                  await onApprove(proposal.proposalId);
                  setConfirming(null);
                  setLoading(false);
                }}
                disabled={loading}
              >
                {loading ? "..." : t("approve")}
              </button>
              <button className="btn-ghost text-sm" onClick={() => setConfirming(null)}>
                Cancel
              </button>
            </div>
          ) : confirming === "reject" ? (
            <div className="flex items-center gap-3">
              <span className="text-red-300 text-sm">{t("rejectConfirm")}</span>
              <button
                className="btn-danger text-sm"
                onClick={async () => {
                  setLoading(true);
                  await onReject(proposal.proposalId);
                  setConfirming(null);
                  setLoading(false);
                }}
                disabled={loading}
              >
                {loading ? "..." : t("reject")}
              </button>
              <button className="btn-ghost text-sm" onClick={() => setConfirming(null)}>
                Cancel
              </button>
            </div>
          ) : (
            <>
              <button
                className="btn-primary text-sm"
                onClick={() => setConfirming("approve")}
                aria-label={t("approve")}
              >
                ✓ {t("approve")}
              </button>
              <button
                className="btn-danger text-sm"
                onClick={() => setConfirming("reject")}
                aria-label={t("reject")}
              >
                ✗ {t("reject")}
              </button>
            </>
          )}
        </div>
      )}

      {/* Resolved state */}
      {proposal.status !== "PENDING" && (
        <div
          className={`text-xs px-2 py-1 rounded inline-flex ${
            proposal.status === "APPROVED"
              ? "bg-green-950 text-green-400"
              : "bg-red-950 text-red-400"
          }`}
        >
          {proposal.status} — {proposal.resolvedBy}
        </div>
      )}
    </div>
  );
}

export function ScheduleProposalList() {
  const t = useTranslations("schedule");
  const tc = useTranslations("common");
  const tp = useTranslations("proposal");
  const [proposals, setProposals] = useState<ScheduleProposal[]>([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    try {
      const data = await apiClient.listProposals();
      setProposals(data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    const interval = setInterval(load, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleApprove = async (id: string) => {
    await apiClient.approveProposal(id, "production_manager");
    await load();
  };

  const handleReject = async (id: string) => {
    await apiClient.rejectProposal(id, "production_manager", "Rejected by production manager");
    await load();
  };

  const pending = proposals.filter((p) => p.status === "PENDING");
  const resolved = proposals.filter((p) => p.status !== "PENDING");

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-white mb-3">{t("proposals")}</h2>
        {loading ? (
          <div className="text-neutral-400 text-sm">{tc("loading")}</div>
        ) : pending.length === 0 ? (
          <div className="text-neutral-500 text-sm card">{tp("noProposals")}</div>
        ) : (
          <div className="space-y-4">
            {pending.map((p) => (
              <ProposalCard
                key={p.proposalId}
                proposal={p}
                onApprove={handleApprove}
                onReject={handleReject}
              />
            ))}
          </div>
        )}
      </div>

      {resolved.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-neutral-400 mb-2">Resolved</h3>
          <div className="space-y-2">
            {resolved.map((p) => (
              <ProposalCard
                key={p.proposalId}
                proposal={p}
                onApprove={handleApprove}
                onReject={handleReject}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
