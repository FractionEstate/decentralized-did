import { IonButton, IonIcon } from "@ionic/react";
import {
  calendarNumberOutline,
  keyOutline,
  refreshOutline,
} from "ionicons/icons";
import { useCallback, useState } from "react";
import { i18n } from "../../../../../i18n";
import { useAppSelector } from "../../../../../store/hooks";
import { getMultisigConnectionsCache } from "../../../../../store/reducers/connectionsCache";
import { getIdentifiersCache } from "../../../../../store/reducers/identifiersCache";
import { getAuthentication } from "../../../../../store/reducers/stateCache";
import { CardDetailsContent } from "../../../card/CardDetails/CardDetailsContent/CardDetailsContent";
import {
  CardDetailsBlock,
} from "../../../card/CardDetails/CardDetailsBlock";
import { CardDetailsItem } from "../../../card/CardDetails/CardDetailsItem";
import { ListHeader } from "../../../ListHeader";
import {
  formatShortDate,
  formatTimeToSec,
  getUTCOffset,
} from "../../../../utils/formatters";
import { IdentifierAttributeDetailModal } from "./IdentifierAttributeDetailModal/IdentifierAttributeDetailModal";
import { DetailView } from "./IdentifierAttributeDetailModal/IdentifierAttributeDetailModal.types";
import { IdentifierContentProps } from "./IdentifierContent.types";
import { FallbackIcon } from "../../../FallbackIcon/FallbackIcon";

const DISPLAY_MEMBERS = 3;

const IdentifierContent = ({
  cardData,
  onRotateKey,
}: IdentifierContentProps) => {
  const identifiersData = useAppSelector(getIdentifiersCache);
  const userName = useAppSelector(getAuthentication)?.userName;
  const multisignConnectionsCache = useAppSelector(getMultisigConnectionsCache);
  const memberCount = cardData.members?.length || 0;
  const [openDetailModal, setOpenDetailModal] = useState(false);
  const [viewType, setViewType] = useState(DetailView.AdvancedDetail);

  const openPropDetailModal = useCallback((view: DetailView) => {
    setViewType(view);
    setOpenDetailModal(true);
  }, []);

  const isMultiSig =
    cardData.groupMemberPre || identifiersData[cardData.id]?.groupMemberPre;

  const members = cardData.members
    ?.map((member: any) => {
      const memberConnection = multisignConnectionsCache[member];
      let name = memberConnection?.label || member;

      if (!memberConnection?.label) {
        name = userName;
      }

      return name;
    })
    .slice(0, DISPLAY_MEMBERS);

  const openGroupMember = () => openPropDetailModal(DetailView.GroupMember);

  return (
    <>
      {isMultiSig && members && (
        <>
          <ListHeader title={i18n.t("tabs.identifiers.details.group.title")} />
          <CardDetailsBlock
            onClick={openGroupMember}
            title={i18n.t("tabs.identifiers.details.group.groupmembers.title")}
            data-testid="group-member-block"
          >
            {members.map((item: any, index: any) => {
              return (
                <CardDetailsItem
                  key={index}
                  info={item}
                  startSlot={<FallbackIcon />}
                  className="member"
                  data-testid={`group-member-${index}`}
                />
              );
            })}
            {members.length < memberCount && (
              <IonButton
                className="view-more-members"
                onClick={() => openPropDetailModal(DetailView.GroupMember)}
                data-testid="view-member"
              >
                {i18n.t("tabs.identifiers.details.group.button.viewmore", {
                  remainMembers: memberCount - DISPLAY_MEMBERS,
                })}
              </IonButton>
            )}
          </CardDetailsBlock>
          {cardData.kt && (
            <CardDetailsBlock
              title={i18n.t(
                "tabs.identifiers.details.group.signingkeysthreshold.title"
              )}
              onClick={() => openPropDetailModal(DetailView.SigningThreshold)}
              data-testid="signing-threshold-block"
            >
              <CardDetailsContent
                mainContent={`${cardData.kt}`}
                subContent={`${i18n.t(
                  "tabs.identifiers.details.group.signingkeysthreshold.outof",
                  { threshold: memberCount }
                )}`}
                data-testid="signing-threshold-content"
              />
            </CardDetailsBlock>
          )}
        </>
      )}
      <ListHeader
        title={i18n.t("tabs.identifiers.details.identifierdetail.title")}
      />
      <div className="identifier-details-split-section">
        <CardDetailsBlock
          title={i18n.t(
            "tabs.identifiers.details.identifierdetail.identifierid.title"
          )}
          data-testid="identifier-id-block"
        >
          <CardDetailsItem
            info={`${cardData.id.substring(0, 5)}...${cardData.id.slice(-5)}`}
            icon={keyOutline}
            data-testid="identifier-id"
            className="identifier-id"
            mask={false}
          />
        </CardDetailsBlock>
        <CardDetailsBlock
          title={i18n.t(
            "tabs.identifiers.details.identifierdetail.created.title"
          )}
          data-testid="created-block"
        >
          <CardDetailsItem
            keyValue={formatShortDate(cardData.createdAtUTC)}
            info={`${formatTimeToSec(cardData.createdAtUTC)} (${getUTCOffset(
              cardData.createdAtUTC
            )})`}
            icon={calendarNumberOutline}
            data-testid="creation-timestamp"
            className="creation-timestamp"
            mask={false}
            fullText
          />
        </CardDetailsBlock>
      </div>
      {!isMultiSig && cardData.k.length && (
        <>
          <CardDetailsBlock
            title={i18n.t(
              "tabs.identifiers.details.identifierdetail.signingkey.title"
            )}
            data-testid="signingkey-block"
          >
            {cardData.k.map((item: any, index: any) => {
              return (
                <CardDetailsItem
                  key={item}
                  info={`${item.substring(0, 5)}...${item.slice(-5)}`}
                  data-testid={`signing-key-${index}`}
                  icon={keyOutline}
                  mask={false}
                  fullText={false}
                />
              );
            })}
          </CardDetailsBlock>
          <CardDetailsBlock
            className="rotate-button-container"
            data-testid="rotate-button-block"
          >
            <IonButton
              shape="round"
              className="rotate-keys-button"
              data-testid="rotate-keys-button"
              onClick={onRotateKey}
            >
              <p>
                {i18n.t(
                  "tabs.identifiers.details.identifierdetail.signingkey.rotate"
                )}
              </p>
              <IonIcon icon={refreshOutline} />
            </IonButton>
          </CardDetailsBlock>
        </>
      )}
      <CardDetailsBlock
        title={i18n.t("tabs.identifiers.details.identifierdetail.showadvanced")}
        onClick={() => openPropDetailModal(DetailView.AdvancedDetail)}
        data-testid="show-advanced-block"
      />
      {isMultiSig && cardData.kt && (
        <>
          <ListHeader
            title={i18n.t("tabs.identifiers.details.keyrotation.title")}
          />
          <CardDetailsBlock
            title={i18n.t(
              "tabs.identifiers.details.keyrotation.rotatesigningkey.title"
            )}
            onClick={() => openPropDetailModal(DetailView.RotationThreshold)}
            data-testid="rotate-signing-key-block"
          >
            <CardDetailsContent
              data-testid="rotate-signing-key"
              mainContent={`${cardData.kt}`}
              subContent={`${i18n.t(
                "tabs.identifiers.details.keyrotation.rotatesigningkey.outof",
                { threshold: memberCount }
              )}`}
            />
          </CardDetailsBlock>
        </>
      )}
      {cardData.kt && (
        <CardDetailsBlock
          title={i18n.t(
            "tabs.identifiers.details.group.signingkeysthreshold.title"
          )}
          onClick={() => openPropDetailModal(DetailView.SigningThreshold)}
          data-testid="signing-threshold-block"
        >
          <CardDetailsContent
            mainContent={`${cardData.kt}`}
            subContent={`${i18n.t(
              "tabs.identifiers.details.group.signingkeysthreshold.outof",
              { threshold: memberCount }
            )}`}
            data-testid="signing-threshold-content"
          />
        </CardDetailsBlock>
      )}
      <IdentifierAttributeDetailModal
        isOpen={openDetailModal}
        setOpen={setOpenDetailModal}
        view={viewType}
        setViewType={setViewType}
        data={cardData}
      />
    </>
  );
};

export { IdentifierContent };
