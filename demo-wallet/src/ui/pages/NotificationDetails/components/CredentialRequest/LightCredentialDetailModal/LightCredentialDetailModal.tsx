import { useEffect, useState } from "react";
import { CredentialDetailModule } from "../../../../../components/credential/CredentialDetailModule/CredentialDetailModule";
import { LightCredentialDetailModalProps } from "./LightCredentialDetailModal.type";

const LightCredentialDetailModal = ({
  credId,
  isOpen,
  defaultSelected,
  joinedCredRequestMembers,
  setIsOpen,
  onClose,
  viewOnly,
}: LightCredentialDetailModalProps) => {
  const [isSelected, setSelected] = useState(!!defaultSelected);

  useEffect(() => {
    setSelected(!!defaultSelected);
  }, [defaultSelected]);

  return (
    <CredentialDetailModule
      pageId="request-cred-detail"
      id={credId || ""}
      onClose={(reason: any) => {
        onClose?.(reason, isSelected, credId);
      }}
      isLightMode
      selected={isSelected}
      setSelected={setSelected}
      joinedCredRequestMembers={joinedCredRequestMembers}
      viewOnly={viewOnly}
    />
  );
};
export { LightCredentialDetailModal };
