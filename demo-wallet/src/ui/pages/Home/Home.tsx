import { IonRefresher, IonRefresherContent, useIonViewWillEnter } from "@ionic/react";
import { useEffect, useState } from "react";
import { useAppDispatch, useAppSelector } from "../../../store/hooks";
import {
  fetchBalance,
  fetchNFTs,
  fetchTransactionHistory,
  getCurrentAddressData,
  setCurrentAddress,
} from "../../../store/reducers/tokensCache";
import { TabLayout } from "../../components/layout/TabLayout";
import { showError } from "../../utils/error";
import BalanceCard from "./components/BalanceCard";
import QuickActions from "./components/QuickActions";
import AssetsList from "./components/AssetsList";
import ActivityFeed from "./components/ActivityFeed";
import AdvancedFeatures from "./components/AdvancedFeatures";
import { useHistory } from "react-router-dom";
import { TabsRoutePath } from "../../../routes/paths";
import "./Home.scss";

// Placeholder address - in production this would come from wallet state
const DEMO_ADDRESS = "addr1qx2fxv2umyhttkxyxp8x0dlpdt3k6cwng5pxj3jhsydzer3n0d3vllmyqwsx5wktcd8cc3sq835lu7drv2xwl2wywfgse35a3x";

const Home = () => {
  const dispatch = useAppDispatch();
  const history = useHistory();
  const addressData = useAppSelector(getCurrentAddressData);

  useIonViewWillEnter(() => {
    // Set current address and load data
    dispatch(setCurrentAddress(DEMO_ADDRESS));
    loadWalletData();
  });

  const loadWalletData = () => {
    try {
      dispatch(fetchBalance(DEMO_ADDRESS));
      dispatch(fetchNFTs(DEMO_ADDRESS));
      dispatch(fetchTransactionHistory({ address: DEMO_ADDRESS, limit: 10 }));
    } catch (error) {
      showError("Failed to load wallet data", error, dispatch);
    }
  };

  const handleRefresh = (event: CustomEvent) => {
    loadWalletData();
    setTimeout(() => {
      event.detail.complete();
    }, 1000);
  };

  // Quick Actions handlers
  const handleSend = () => {
    // TODO: Navigate to send page or open send modal
    console.log("Send action - TODO: Implement send functionality");
  };

  const handleReceive = () => {
    // TODO: Navigate to receive page or show QR code
    console.log("Receive action - TODO: Implement receive functionality");
  };

  const handleBuy = () => {
    // TODO: Navigate to buy page or external service
    console.log("Buy action - TODO: Implement buy functionality");
  };

  // Advanced Features handlers
  const handleStakingClick = () => {
    history.push(TabsRoutePath.STAKING);
  };

  const handleGovernanceClick = () => {
    history.push(TabsRoutePath.GOVERNANCE);
  };

  const handleBrowserClick = () => {
    history.push(TabsRoutePath.DAPP_BROWSER);
  };

  const handleBiometricClick = () => {
    history.push(TabsRoutePath.IDENTIFIERS);
  };

  // Asset and transaction handlers
  const handleAssetClick = (asset: any) => {
    // TODO: Navigate to asset details or token page
    console.log("Asset clicked:", asset);
  };

  const handleTransactionClick = (transaction: any) => {
    // TODO: Navigate to transaction details
    console.log("Transaction clicked:", transaction);
  };

  return (
    <TabLayout
      pageId="home-page"
      header={false}
      customClass="home-page biometric-brand"
    >
      <IonRefresher slot="fixed" onIonRefresh={handleRefresh}>
        <IonRefresherContent />
      </IonRefresher>

      <div className="home-content">
        {/* Balance Card */}
        <BalanceCard
          balance={addressData?.balance}
          isLoading={addressData?.isLoading}
          error={addressData?.error}
        />

        {/* Quick Actions */}
        <QuickActions
          onSend={handleSend}
          onReceive={handleReceive}
          onBuy={handleBuy}
        />

        {/* Assets List */}
        <AssetsList
          assets={addressData?.balance?.assets}
          isLoading={addressData?.isLoading}
          error={addressData?.error}
          onAssetClick={handleAssetClick}
        />

        {/* Recent Activity */}
        <ActivityFeed
          transactions={addressData?.transactions}
          isLoading={addressData?.isLoading}
          error={addressData?.error}
          onTransactionClick={handleTransactionClick}
        />

        {/* Advanced Features with Biometric Branding */}
        <div className="biometric-brand">
          <AdvancedFeatures
            onStakingClick={handleStakingClick}
            onGovernanceClick={handleGovernanceClick}
            onBrowserClick={handleBrowserClick}
            onBiometricClick={handleBiometricClick}
          />
        </div>
      </div>
    </TabLayout>
  );
};

export default Home;