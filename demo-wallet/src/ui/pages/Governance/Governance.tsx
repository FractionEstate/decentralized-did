import { IonRefresher, IonRefresherContent, useIonViewWillEnter } from "@ionic/react";
import { useState } from "react";
import { useAppDispatch, useAppSelector } from "../../../store/hooks";
import {
  fetchDReps,
  fetchProposals,
  fetchVotingPower,
  selectDReps,
  selectProposals,
  selectGovernanceLoading,
  selectGovernanceError,
} from "../../../store/reducers/governanceCache";
import { TabLayout } from "../../components/layout/TabLayout/TabLayout";
import { showError } from "../../utils/error";
import { formatVotingPower, getStatusColor, formatProposalId } from "../../../core/cardano/governanceService";
import "./Governance.scss";

// Placeholder stake address - in production this would come from wallet state
const DEMO_STAKE_ADDRESS = "stake1ux2fxv2umyhttkxyxp8x0dlpdt3k6cwng5pxj3jhsydzer3qf0000";

const Governance = () => {
  const dispatch = useAppDispatch();
  const dreps = useAppSelector((state) => selectDReps(state));
  const proposals = useAppSelector((state) => selectProposals(state, 'all'));
  const loading = useAppSelector(selectGovernanceLoading);
  const error = useAppSelector(selectGovernanceError);
  const [activeTab, setActiveTab] = useState<"dreps" | "proposals" | "votes">("proposals");

  useIonViewWillEnter(() => {
    loadGovernanceData();
  });

  const loadGovernanceData = () => {
    try {
      dispatch(fetchDReps({ limit: 20, offset: 0 }));
      dispatch(fetchProposals({ limit: 20, offset: 0 }));
      dispatch(fetchVotingPower(DEMO_STAKE_ADDRESS));
    } catch (err) {
      showError("Failed to load governance data", err, dispatch);
    }
  };

  const handleRefresh = (event: CustomEvent) => {
    loadGovernanceData();
    setTimeout(() => {
      event.detail.complete();
    }, 1000);
  };

  const renderDReps = () => {
    if (loading.dreps && dreps.length === 0) {
      return <div className="loading-placeholder">Loading DReps...</div>;
    }

    if (error.dreps) {
      return <div className="error-message">Error: {error.dreps}</div>;
    }

    if (dreps.length === 0) {
      return <div className="empty-state">No DReps found. Governance data may not be available yet on this network.</div>;
    }

    return (
      <div className="dreps-list">
        {dreps.map((drep) => (
          <div key={drep.drep_id} className="drep-card">
            <div className="drep-header">
              <h3>{drep.metadata?.name || formatProposalId(drep.drep_id)}</h3>
              <span className={`status ${drep.active ? 'active' : 'inactive'}`}>
                {drep.active ? 'Active' : 'Inactive'}
              </span>
            </div>
            {drep.metadata?.description && (
              <p className="drep-description">{drep.metadata.description}</p>
            )}
            <div className="drep-metrics">
              <div className="metric">
                <span className="label">Voting Power</span>
                <span className="value">{formatVotingPower(drep.voting_power)}</span>
              </div>
              <div className="metric">
                <span className="label">Delegators</span>
                <span className="value">{drep.delegators}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  };

  const renderProposals = () => {
    if (loading.proposals && proposals.length === 0) {
      return <div className="loading-placeholder">Loading proposals...</div>;
    }

    if (error.proposals) {
      return <div className="error-message">Error: {error.proposals}</div>;
    }

    if (proposals.length === 0) {
      return <div className="empty-state">No proposals found. Governance actions may not be available yet on this network.</div>;
    }

    return (
      <div className="proposals-list">
        {proposals.map((proposal) => (
          <div key={proposal.proposal_id} className="proposal-card">
            <div className="proposal-header">
              <h3>{proposal.title}</h3>
              <span
                className="status"
                style={{ backgroundColor: getStatusColor(proposal.status) }}
              >
                {proposal.status}
              </span>
            </div>
            {proposal.description && (
              <p className="proposal-description">{proposal.description}</p>
            )}
            <div className="proposal-votes">
              <div className="vote-bar">
                <div
                  className="vote-yes"
                  style={{ width: `${(proposal.yes_votes / proposal.total_votes * 100) || 0}%` }}
                />
                <div
                  className="vote-no"
                  style={{ width: `${(proposal.no_votes / proposal.total_votes * 100) || 0}%` }}
                />
              </div>
              <div className="vote-counts">
                <span className="yes">Yes: {proposal.yes_votes}</span>
                <span className="no">No: {proposal.no_votes}</span>
                <span className="abstain">Abstain: {proposal.abstain_votes}</span>
              </div>
              <div className="approval">
                Approval: {proposal.approval_percentage.toFixed(1)}%
              </div>
            </div>
            <div className="proposal-meta">
              <span>ID: {formatProposalId(proposal.proposal_id)}</span>
              <span>Total Votes: {proposal.total_votes}</span>
            </div>
          </div>
        ))}
      </div>
    );
  };

  const renderVotes = () => {
    return (
      <div className="votes-section">
        <div className="info-message">
          Vote history will be displayed here once you participate in governance.
          Connect your wallet to view your voting history.
        </div>
      </div>
    );
  };

  return (
    <TabLayout
      header={false}
    >
      <IonRefresher slot="fixed" onIonRefresh={handleRefresh}>
        <IonRefresherContent />
      </IonRefresher>

      <div className="governance-page">
        <div className="tabs">
          <button
            className={activeTab === "dreps" ? "active" : ""}
            onClick={() => setActiveTab("dreps")}
          >
            DReps
          </button>
          <button
            className={activeTab === "proposals" ? "active" : ""}
            onClick={() => setActiveTab("proposals")}
          >
            Proposals
          </button>
          <button
            className={activeTab === "votes" ? "active" : ""}
            onClick={() => setActiveTab("votes")}
          >
            My Votes
          </button>
        </div>

        <div className="tab-content">
          {activeTab === "dreps" && renderDReps()}
          {activeTab === "proposals" && renderProposals()}
          {activeTab === "votes" && renderVotes()}
        </div>
      </div>
    </TabLayout>
  );
};

export default Governance;
