import { IonSkeletonText } from "@ionic/react";
import "./LoadingSkeleton.scss";

interface LoadingSkeletonProps {
  count?: number;
  variant?: "text" | "card" | "list" | "page";
  animated?: boolean;
}

const LoadingSkeleton = ({
  count = 3,
  variant = "text",
  animated = true,
}: LoadingSkeletonProps) => {
  if (variant === "text") {
    return (
      <div className="loading-skeleton loading-skeleton-text">
        {Array.from({ length: count }).map((_, index) => (
          <IonSkeletonText
            key={index}
            animated={animated}
            className="skeleton-line"
          />
        ))}
      </div>
    );
  }

  if (variant === "card") {
    return (
      <div className="loading-skeleton loading-skeleton-card">
        <div className="skeleton-card-header">
          <IonSkeletonText
            animated={animated}
            className="skeleton-avatar"
          />
          <div className="skeleton-card-title">
            <IonSkeletonText
              animated={animated}
              className="skeleton-title"
            />
            <IonSkeletonText
              animated={animated}
              className="skeleton-subtitle"
            />
          </div>
        </div>
        <div className="skeleton-card-content">
          {Array.from({ length: count }).map((_, index) => (
            <IonSkeletonText
              key={index}
              animated={animated}
              className="skeleton-line"
            />
          ))}
        </div>
      </div>
    );
  }

  if (variant === "list") {
    return (
      <div className="loading-skeleton loading-skeleton-list">
        {Array.from({ length: count }).map((_, index) => (
          <div key={index} className="skeleton-list-item">
            <IonSkeletonText
              animated={animated}
              className="skeleton-avatar-small"
            />
            <div className="skeleton-list-content">
              <IonSkeletonText
                animated={animated}
                className="skeleton-line skeleton-line-full"
              />
              <IonSkeletonText
                animated={animated}
                className="skeleton-line skeleton-line-short"
              />
            </div>
          </div>
        ))}
      </div>
    );
  }

  // Page variant - full page skeleton
  return (
    <div className="loading-skeleton loading-skeleton-page">
      <div className="skeleton-page-header">
        <IonSkeletonText
          animated={animated}
          className="skeleton-header-title"
        />
      </div>
      <div className="skeleton-page-content">
        {Array.from({ length: count }).map((_, index) => (
          <div key={index} className="skeleton-section">
            <IonSkeletonText
              animated={animated}
              className="skeleton-section-title"
            />
            <div className="skeleton-section-items">
              {Array.from({ length: 2 }).map((_, itemIndex) => (
                <IonSkeletonText
                  key={itemIndex}
                  animated={animated}
                  className="skeleton-line"
                />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export { LoadingSkeleton };
