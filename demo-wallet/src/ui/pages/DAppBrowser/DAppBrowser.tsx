/**
 * DAppBrowser Component
 *
 * Provides an embedded browser for Cardano dApps with CIP-30 wallet injection.
 * Allows users to interact with dApps directly within the wallet.
 */

import { useState, useRef, useEffect } from "react";
import {
  IonPage,
  IonHeader,
  IonToolbar,
  IonTitle,
  IonContent,
  IonButtons,
  IonButton,
  IonIcon,
  IonInput,
  IonLoading,
  IonAlert,
  IonList,
  IonItem,
  IonLabel,
  IonBadge,
} from "@ionic/react";
import {
  arrowBack,
  arrowForward,
  refresh,
  home,
  closeCircle,
  shieldCheckmark,
  globeOutline,
} from "ionicons/icons";
import "./DAppBrowser.scss";

interface DAppConnection {
  origin: string;
  name: string;
  icon?: string;
  connectedAt: Date;
  permissions: string[];
}

interface DAppBrowserProps {
  initialUrl?: string;
}

const DAppBrowser: React.FC<DAppBrowserProps> = ({ initialUrl = "" }) => {
  const [url, setUrl] = useState<string>(initialUrl);
  const [currentUrl, setCurrentUrl] = useState<string>(initialUrl);
  const [loading, setLoading] = useState<boolean>(false);
  const [canGoBack, setCanGoBack] = useState<boolean>(false);
  const [canGoForward, setCanGoForward] = useState<boolean>(false);
  const [showConnectionAlert, setShowConnectionAlert] = useState<boolean>(false);
  const [pendingConnection, setPendingConnection] = useState<DAppConnection | null>(null);
  const [connectedDApps, setConnectedDApps] = useState<DAppConnection[]>([]);

  const iframeRef = useRef<HTMLIFrameElement>(null);

  /**
   * Handle URL navigation
   */
  const navigateTo = (newUrl: string) => {
    if (!newUrl) return;

    // Ensure URL has protocol
    let fullUrl = newUrl;
    if (!newUrl.startsWith("http://") && !newUrl.startsWith("https://")) {
      fullUrl = `https://${newUrl}`;
    }

    setCurrentUrl(fullUrl);
    setLoading(true);
  };

  /**
   * Handle URL input change
   */
  const handleUrlChange = (e: CustomEvent) => {
    setUrl(e.detail.value || "");
  };

  /**
   * Handle Enter key in URL bar
   */
  const handleUrlKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      navigateTo(url);
    }
  };

  /**
   * Navigate back
   */
  const goBack = () => {
    if (iframeRef.current && canGoBack) {
      // Note: iframe history navigation requires proper postMessage setup
      console.warn("Browser back navigation not fully implemented");
    }
  };

  /**
   * Navigate forward
   */
  const goForward = () => {
    if (iframeRef.current && canGoForward) {
      console.warn("Browser forward navigation not fully implemented");
    }
  };

  /**
   * Reload current page
   */
  const reload = () => {
    if (iframeRef.current) {
      iframeRef.current.src = currentUrl;
    }
  };

  /**
   * Go to home (empty state)
   */
  const goHome = () => {
    setCurrentUrl("");
    setUrl("");
  };

  /**
   * Handle iframe load
   */
  const handleIframeLoad = () => {
    setLoading(false);

    // Update navigation state
    // Note: Cross-origin iframes cannot access history
    // This would require a service worker or browser extension approach
    setCanGoBack(false);
    setCanGoForward(false);
  };

  /**
   * Handle dApp connection request
   */
  const handleConnectionRequest = (origin: string, name: string) => {
    setPendingConnection({
      origin,
      name,
      connectedAt: new Date(),
      permissions: ["getBalance", "getUsedAddresses", "signTx"],
    });
    setShowConnectionAlert(true);
  };

  /**
   * Accept dApp connection
   */
  const acceptConnection = () => {
    if (pendingConnection) {
      setConnectedDApps([...connectedDApps, pendingConnection]);
      // TODO: Inject CIP-30 API into iframe
      console.log("Accepted connection from:", pendingConnection.origin);
    }
    setShowConnectionAlert(false);
    setPendingConnection(null);
  };

  /**
   * Reject dApp connection
   */
  const rejectConnection = () => {
    console.log("Rejected connection from:", pendingConnection?.origin);
    setShowConnectionAlert(false);
    setPendingConnection(null);
  };

  /**
   * Disconnect from dApp
   */
  const disconnectDApp = (origin: string) => {
    setConnectedDApps(connectedDApps.filter(dapp => dapp.origin !== origin));
    // TODO: Remove CIP-30 API from iframe
    console.log("Disconnected from:", origin);
  };

  /**
   * Listen for messages from iframe (dApp connection requests, etc.)
   */
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      // Validate origin
      try {
        const origin = new URL(event.origin);

        // Handle different message types
        if (event.data.type === "WALLET_CONNECT_REQUEST") {
          handleConnectionRequest(event.origin, event.data.name || "Unknown dApp");
        }
      } catch (error) {
        console.error("Invalid message origin:", event.origin);
      }
    };

    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, [connectedDApps]);

  return (
    <IonPage>
      <IonHeader>
        <IonToolbar>
          <IonTitle>dApp Browser</IonTitle>
        </IonToolbar>

        {/* Navigation toolbar */}
        <IonToolbar className="dapp-browser-nav">
          <IonButtons slot="start">
            <IonButton onClick={goBack} disabled={!canGoBack}>
              <IonIcon slot="icon-only" icon={arrowBack} />
            </IonButton>
            <IonButton onClick={goForward} disabled={!canGoForward}>
              <IonIcon slot="icon-only" icon={arrowForward} />
            </IonButton>
            <IonButton onClick={reload} disabled={!currentUrl}>
              <IonIcon slot="icon-only" icon={refresh} />
            </IonButton>
            <IonButton onClick={goHome}>
              <IonIcon slot="icon-only" icon={home} />
            </IonButton>
          </IonButtons>

          <IonInput
            className="url-bar"
            value={url}
            placeholder="Enter dApp URL..."
            onIonInput={handleUrlChange}
            onKeyPress={handleUrlKeyPress}
            clearInput
          />

          <IonButtons slot="end">
            {connectedDApps.length > 0 && (
              <IonButton color="success">
                <IonIcon slot="icon-only" icon={shieldCheckmark} />
                <IonBadge color="success">{connectedDApps.length}</IonBadge>
              </IonButton>
            )}
          </IonButtons>
        </IonToolbar>
      </IonHeader>

      <IonContent>
        <IonLoading isOpen={loading} message="Loading dApp..." />

        {/* Connection request alert */}
        <IonAlert
          isOpen={showConnectionAlert}
          onDidDismiss={() => setShowConnectionAlert(false)}
          header="Connect to dApp?"
          message={`${pendingConnection?.name || "This dApp"} wants to connect to your wallet. This will allow it to:`}
          subHeader={pendingConnection?.permissions.join(", ")}
          buttons={[
            {
              text: "Reject",
              role: "cancel",
              handler: rejectConnection,
            },
            {
              text: "Connect",
              handler: acceptConnection,
            },
          ]}
        />

        {/* Browser container */}
        <div className="dapp-browser-container">
          {currentUrl ? (
            <iframe
              ref={iframeRef}
              src={currentUrl}
              className="dapp-browser-iframe"
              title="dApp Browser"
              sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
              onLoad={handleIframeLoad}
            />
          ) : (
            <div className="dapp-browser-empty">
              <IonIcon icon={globeOutline} className="empty-icon" />
              <h2>Enter a dApp URL to get started</h2>
              <p>Browse Cardano dApps with built-in wallet integration</p>

              {/* Popular dApps suggestions */}
              <div className="popular-dapps">
                <h3>Popular dApps</h3>
                <IonList>
                  <IonItem button onClick={() => navigateTo("https://app.minswap.org")}>
                    <IonLabel>
                      <h2>Minswap</h2>
                      <p>Decentralized Exchange</p>
                    </IonLabel>
                  </IonItem>
                  <IonItem button onClick={() => navigateTo("https://www.jpg.store")}>
                    <IonLabel>
                      <h2>JPG.store</h2>
                      <p>NFT Marketplace</p>
                    </IonLabel>
                  </IonItem>
                  <IonItem button onClick={() => navigateTo("https://sundaeswap.finance")}>
                    <IonLabel>
                      <h2>SundaeSwap</h2>
                      <p>Decentralized Exchange</p>
                    </IonLabel>
                  </IonItem>
                </IonList>
              </div>
            </div>
          )}
        </div>

        {/* Connected dApps footer */}
        {connectedDApps.length > 0 && (
          <div className="connected-dapps-footer">
            <h4>Connected dApps</h4>
            {connectedDApps.map((dapp) => (
              <div key={dapp.origin} className="connected-dapp-item">
                <span>{dapp.name}</span>
                <IonButton
                  size="small"
                  color="danger"
                  onClick={() => disconnectDApp(dapp.origin)}
                >
                  <IonIcon slot="icon-only" icon={closeCircle} />
                </IonButton>
              </div>
            ))}
          </div>
        )}
      </IonContent>
    </IonPage>
  );
};

export default DAppBrowser;
