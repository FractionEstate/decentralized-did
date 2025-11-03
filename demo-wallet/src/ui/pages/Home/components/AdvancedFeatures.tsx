import { IonIcon } from "@ionic/react";
import { 
  trophy, 
  documentText, 
  globe, 
  shield, 
  fingerPrint,
  stats
} from "ionicons/icons";
import "./AdvancedFeatures.scss";

interface AdvancedFeaturesProps {
  onStakingClick?: () => void;
  onGovernanceClick?: () => void;
  onBrowserClick?: () => void;
  onBiometricClick?: () => void;
}

const AdvancedFeatures: React.FC<AdvancedFeaturesProps> = ({ 
  onStakingClick,
  onGovernanceClick,
  onBrowserClick,
  onBiometricClick
}) => {
  const features = [
    {
      id: 'biometric',
      title: 'Biometric DIDs',
      description: 'Secure identity management',
      icon: fingerPrint,
      gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      onClick: onBiometricClick || (() => console.log('Biometric DIDs clicked'))
    },
    {
      id: 'staking',
      title: 'Staking',
      description: 'Earn rewards with ADA',
      icon: trophy,
      gradient: 'linear-gradient(135deg, #ffd89b 0%, #19547b 100%)',
      onClick: onStakingClick || (() => console.log('Staking clicked'))
    },
    {
      id: 'governance',
      title: 'Governance',
      description: 'Participate in voting',
      icon: documentText,
      gradient: 'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)',
      onClick: onGovernanceClick || (() => console.log('Governance clicked'))
    },
    {
      id: 'browser',
      title: 'DApp Browser',
      description: 'Explore Cardano DApps',
      icon: globe,
      gradient: 'linear-gradient(135deg, #d299c2 0%, #fef9d7 100%)',
      onClick: onBrowserClick || (() => console.log('Browser clicked'))
    }
  ];

  return (
    <div className="advanced-features">
      <div className="features-header">
        <h3>Explore More</h3>
        <p>Advanced features for power users</p>
      </div>
      
      <div className="features-grid">
        {features.map((feature) => (
          <div 
            key={feature.id}
            className="feature-card"
            onClick={feature.onClick}
          >
            <div 
              className="feature-icon"
              style={{ background: feature.gradient }}
            >
              <IonIcon icon={feature.icon} />
            </div>
            <div className="feature-content">
              <h4 className="feature-title">{feature.title}</h4>
              <p className="feature-description">{feature.description}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default AdvancedFeatures;