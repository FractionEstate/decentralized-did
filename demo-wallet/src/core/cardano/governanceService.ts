/**
 * Governance Service - API client for CIP-1694 governance operations
 * Provides methods for DRep queries, proposal fetching, and vote tracking
 */

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const REQUEST_TIMEOUT = 15000; // 15 seconds

// Type definitions matching backend models
export interface DRep {
  drep_id: string;
  voting_power: number;
  delegators: number;
  active: boolean;
  metadata?: {
    name?: string;
    description?: string;
    url?: string;
  };
}

export interface Proposal {
  proposal_id: string;
  title: string;
  description?: string;
  status: 'active' | 'passed' | 'rejected' | 'expired';
  submitted_at: string;
  expires_at?: string;
  yes_votes: number;
  no_votes: number;
  abstain_votes: number;
  total_votes: number;
  approval_percentage: number;
  metadata?: Record<string, any>;
}

export interface Vote {
  vote_id: string;
  proposal_id: string;
  voter: string;
  vote: 'yes' | 'no' | 'abstain';
  voting_power: number;
  timestamp: string;
}

export interface VotingPower {
  stake_address: string;
  voting_power: number;
  delegated_to?: string;
  can_vote: boolean;
}

export interface VoteHistory {
  votes: Vote[];
  total: number;
}

/**
 * Governance Service singleton
 */
class GovernanceService {
  private static instance: GovernanceService;

  private constructor() {}

  static getInstance(): GovernanceService {
    if (!GovernanceService.instance) {
      GovernanceService.instance = new GovernanceService();
    }
    return GovernanceService.instance;
  }

  /**
   * Fetch DRep directory
   */
  async getDReps(limit: number = 20, offset: number = 0): Promise<DRep[]> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);

    try {
      const response = await fetch(
        `${API_BASE}/api/governance/dreps?limit=${limit}&offset=${offset}`,
        { signal: controller.signal }
      );

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`Failed to fetch DReps: ${response.statusText}`);
      }

      const data = await response.json();
      return data.dreps || [];
    } catch (error: any) {
      if (error.name === 'AbortError') {
        console.error('getDReps request timed out');
        throw new Error('Request timed out');
      }
      console.error('Error fetching DReps:', error);
      throw error;
    }
  }

  /**
   * Fetch specific DRep details
   */
  async getDRepInfo(drepId: string): Promise<DRep> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);

    try {
      const response = await fetch(
        `${API_BASE}/api/governance/drep/${encodeURIComponent(drepId)}`,
        { signal: controller.signal }
      );

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`Failed to fetch DRep info: ${response.statusText}`);
      }

      return await response.json();
    } catch (error: any) {
      if (error.name === 'AbortError') {
        console.error('getDRepInfo request timed out');
        throw new Error('Request timed out');
      }
      console.error('Error fetching DRep info:', error);
      throw error;
    }
  }

  /**
   * Fetch governance proposals
   */
  async getProposals(
    status?: 'active' | 'passed' | 'rejected' | 'expired',
    limit: number = 20,
    offset: number = 0
  ): Promise<Proposal[]> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);

    try {
      const params = new URLSearchParams({
        limit: limit.toString(),
        offset: offset.toString(),
      });
      if (status) {
        params.append('status', status);
      }

      const response = await fetch(
        `${API_BASE}/api/governance/proposals?${params.toString()}`,
        { signal: controller.signal }
      );

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`Failed to fetch proposals: ${response.statusText}`);
      }

      const data = await response.json();
      return data.proposals || [];
    } catch (error: any) {
      if (error.name === 'AbortError') {
        console.error('getProposals request timed out');
        throw new Error('Request timed out');
      }
      console.error('Error fetching proposals:', error);
      throw error;
    }
  }

  /**
   * Fetch votes for a specific proposal
   */
  async getProposalVotes(proposalId: string): Promise<Vote[]> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);

    try {
      const response = await fetch(
        `${API_BASE}/api/governance/proposal/${encodeURIComponent(proposalId)}/votes`,
        { signal: controller.signal }
      );

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`Failed to fetch proposal votes: ${response.statusText}`);
      }

      const data = await response.json();
      return data.votes || [];
    } catch (error: any) {
      if (error.name === 'AbortError') {
        console.error('getProposalVotes request timed out');
        throw new Error('Request timed out');
      }
      console.error('Error fetching proposal votes:', error);
      throw error;
    }
  }

  /**
   * Fetch voting power for a stake address
   */
  async getVotingPower(stakeAddress: string): Promise<VotingPower> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);

    try {
      const response = await fetch(
        `${API_BASE}/api/governance/voting-power/${encodeURIComponent(stakeAddress)}`,
        { signal: controller.signal }
      );

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`Failed to fetch voting power: ${response.statusText}`);
      }

      return await response.json();
    } catch (error: any) {
      if (error.name === 'AbortError') {
        console.error('getVotingPower request timed out');
        throw new Error('Request timed out');
      }
      console.error('Error fetching voting power:', error);
      throw error;
    }
  }

  /**
   * Fetch vote history for a voter (DRep or stake address)
   */
  async getVoteHistory(voter: string, limit: number = 20): Promise<VoteHistory> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);

    try {
      const response = await fetch(
        `${API_BASE}/api/governance/vote-history/${encodeURIComponent(voter)}?limit=${limit}`,
        { signal: controller.signal }
      );

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`Failed to fetch vote history: ${response.statusText}`);
      }

      return await response.json();
    } catch (error: any) {
      if (error.name === 'AbortError') {
        console.error('getVoteHistory request timed out');
        throw new Error('Request timed out');
      }
      console.error('Error fetching vote history:', error);
      throw error;
    }
  }
}

// Utility functions
export function formatVotingPower(power: number): string {
  if (power >= 1_000_000_000) {
    return `${(power / 1_000_000_000).toFixed(2)}B`;
  } else if (power >= 1_000_000) {
    return `${(power / 1_000_000).toFixed(2)}M`;
  } else if (power >= 1_000) {
    return `${(power / 1_000).toFixed(2)}K`;
  }
  return power.toString();
}

export function getVoteColor(vote: 'yes' | 'no' | 'abstain'): string {
  switch (vote) {
    case 'yes':
      return '#22c55e'; // green
    case 'no':
      return '#ef4444'; // red
    case 'abstain':
      return '#94a3b8'; // gray
    default:
      return '#64748b';
  }
}

export function formatProposalId(proposalId: string): string {
  if (proposalId.length > 16) {
    return `${proposalId.slice(0, 8)}...${proposalId.slice(-6)}`;
  }
  return proposalId;
}

export function getStatusColor(status: string): string {
  switch (status) {
    case 'active':
      return '#3b82f6'; // blue
    case 'passed':
      return '#22c55e'; // green
    case 'rejected':
      return '#ef4444'; // red
    case 'expired':
      return '#94a3b8'; // gray
    default:
      return '#64748b';
  }
}

// Export singleton instance getter
export const getGovernanceService = () => GovernanceService.getInstance();

export default GovernanceService;
