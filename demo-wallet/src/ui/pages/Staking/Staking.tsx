import { IonRefresher, IonRefresherContent, useIonViewWillEnter } from "@ionic/react";
import { useState } from "react";
import { useAppDispatch, useAppSelector } from "../../../store/hooks";
import {
  fetchAccountInfo,
  fetchPoolList,
  fetchRewards,
  getAddressData,
  getCurrentStakeAddress,
  getPools,
} from "../../../store/reducers/stakingCache";
import { TabLayout } from "../../components/layout/TabLayout/TabLayout";
import { EmptyState } from "../../components/common/EmptyState";
import { LoadingPlaceholder } from "../../components/common/LoadingPlaceholder";
import { ErrorDisplay } from "../../components/common/ErrorDisplay";
import { showError } from "../../utils/error";
import { StakingService } from "../../../core/cardano/stakingService";
import "./Staking.scss";

// Current stake address comes from store; if missing, UI prompts to connect

const Staking = () => {
  const dispatch = useAppDispatch();
  const currentStakeAddress = useAppSelector(getCurrentStakeAddress);
  const addressData = useAppSelector(
    currentStakeAddress ? getAddressData(currentStakeAddress) : () => undefined
  );
  const pools = useAppSelector(getPools);
  const [activeTab, setActiveTab] = useState<"account" | "pools" | "rewards">("account");

  useIonViewWillEnter(() => {
    if (currentStakeAddress) {
      loadStakingData(currentStakeAddress);
    }
  });

  const loadStakingData = (stakeAddr?: string) => {
    try {
      const addr = stakeAddr || currentStakeAddress;
      if (addr) {
        dispatch(fetchAccountInfo(addr));
        dispatch(fetchRewards(addr));
      }
      dispatch(fetchPoolList());
    } catch (error) {
      showError("Failed to load staking data", error, dispatch);
    }
  };

  const handleRefresh = (event: CustomEvent) => {
    loadStakingData();
    setTimeout(() => {
      event.detail.complete();
    }, 1000);
  };

  const renderAccount = () => {
    if (addressData?.isLoading && !addressData?.account) {
      return <LoadingPlaceholder message="Loading account information..." />;
    }

    if (addressData?.error) {
      return <ErrorDisplay error={addressData.error} onRetry={loadStakingData} title="Failed to Load Account" />;
    }

    const account = addressData?.account;
    if (!account) {
      return <EmptyState icon="trophy-outline" title="No Account Data" description="Unable to load staking account information." actionLabel="Retry" onAction={loadStakingData} />;
    }

    return (
      <div className="account-container">
        <div className="account-card">
          <div className="account-status">
            <div className="status-label">Status</div>
            <div className={`status-badge ${account.status === "registered" ? "active" : "inactive"}`}>
              {account.status}
            </div>
          </div>

          <div className="balance-info">
            <div className="balance-item">
              <div className="label">Total Balance</div>
              <div className="value">{account.total_balance_ada} ₳</div>
            </div>
            <div className="balance-item">
              <div className="label">Available Rewards</div>
              <div className="value success">{account.rewards_ada} ₳</div>
            </div>
          </div>

          {account.is_delegated && account.delegated_pool && (
            <div className="delegation-info">
              <div className="label">Delegated To</div>
              <div className="pool-id">{account.delegated_pool.substring(0, 20)}...</div>
            </div>
          )}

          {!account.is_delegated && (
            <div className="delegation-notice">
              <p>Account not currently delegated to any pool.</p>
              <button className="delegate-button">Select Pool to Delegate</button>
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderPools = () => {
    if (pools.length === 0) {
      return <LoadingPlaceholder message="Loading stake pools..." />;
    }

    return (
      <div className="pools-container">
        <div className="pools-list">
          {pools.slice(0, 10).map((pool) => (
            <div key={pool.pool_id} className="pool-card">
              <div className="pool-header">
                <div className="pool-ticker">{pool.ticker || "Unknown Pool"}</div>
                {pool.estimated_apy && (
                  <div className="pool-apy">{StakingService.formatAPY(pool.estimated_apy)} APY</div>
                )}
              </div>

              {pool.name && <div className="pool-name">{pool.name}</div>}

              <div className="pool-metrics">
                <div className="metric">
                  <span className="metric-label">Stake:</span>
                  <span className="metric-value">{pool.active_stake_ada}</span>
                </div>
                <div className="metric">
                  <span className="metric-label">Margin:</span>
                  <span className="metric-value">{pool.margin_percentage}</span>
                </div>
                <div className="metric">
                  <span className="metric-label">Saturation:</span>
                  <span className={`metric-value ${StakingService.getSaturationColor(pool.live_saturation)}`}>
                    {pool.saturation_percentage}
                  </span>
                </div>
              </div>

              <div className="pool-stats">
                <span>{pool.blocks_minted} blocks</span>
                <span>•</span>
                <span>{pool.live_delegators} delegators</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderRewards = () => {
    if (addressData?.isLoading && !addressData?.rewards) {
      return <LoadingPlaceholder message="Loading rewards history..." />;
    }

    const rewards = addressData?.rewards || [];

    if (rewards.length === 0) {
      return <EmptyState icon="trophy-outline" title="No Rewards" description="Your staking rewards history will appear here once you start earning." />;
    }

    return (
      <div className="rewards-container">
        <div className="rewards-list">
          {rewards.map((reward) => (
            <div key={`${reward.epoch}-${reward.pool_id}`} className="reward-item">
              <div className="reward-header">
                <div className="reward-epoch">Epoch {reward.epoch}</div>
                <div className="reward-amount">{reward.amount_ada} ₳</div>
              </div>
              <div className="reward-details">
                <span>Earned in epoch {reward.earned_epoch}</span>
                <span>•</span>
                <span>{StakingService.formatEpochDate(reward.epoch)}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <TabLayout
      pageId="staking-page"
      header={false}
      customClass="staking-page"
    >
      {!currentStakeAddress && (
        <div className="staking-content">
          <EmptyState
            icon="trophy-outline"
            title="No Wallet Connected"
            description="Connect or select a wallet to view staking account, pools, and rewards."
          />
        </div>
      )}
      <IonRefresher slot="fixed" onIonRefresh={handleRefresh}>
        <IonRefresherContent />
      </IonRefresher>

      {currentStakeAddress && (
        <div className="staking-tabs">
          <button
            className={`tab-button ${activeTab === "account" ? "active" : ""}`}
            onClick={() => setActiveTab("account")}
          >
            Account
          </button>
          <button
            className={`tab-button ${activeTab === "pools" ? "active" : ""}`}
            onClick={() => setActiveTab("pools")}
          >
            Pools
          </button>
          <button
            className={`tab-button ${activeTab === "rewards" ? "active" : ""}`}
            onClick={() => setActiveTab("rewards")}
          >
            Rewards
          </button>
        </div>
      )}

      {currentStakeAddress && (
        <div className="staking-content">
          {activeTab === "account" && renderAccount()}
          {activeTab === "pools" && renderPools()}
          {activeTab === "rewards" && renderRewards()}
        </div>
      )}
    </TabLayout>
  );
};

export default Staking;
