import { IonIcon } from "@ionic/react";
import { star } from "ionicons/icons";
import { i18n } from "../../../../../../i18n";
import { CardDetailsBlock } from "../../../../card/CardDetails";
import { CardDetailsItem } from "../../../../card/CardDetails";
import { ListHeader } from "../../../../ListHeader";
import { ListProps } from "./IdentifierAttributeDetailModal.types";
import { FallbackIcon } from "../../../../FallbackIcon";

const List = ({ data, title, bottomText, fullText, mask }: ListProps) => {
  return (
    <>
      <ListHeader title={title} />
      <CardDetailsBlock
        className="list-item"
      >
        {data.map((item, index) => {
          return (
            <CardDetailsItem
              key={index}
              info={item.title}
              startSlot={<FallbackIcon src={item.image} />}
              className="member"
              testId={`group-member-${item.title}`}
              mask={mask}
              fullText={fullText}
              endSlot={
                item.isCurrentUser && (
                  <div className="user-label">
                    <IonIcon icon={star} />
                    <span>
                      {i18n.t("tabs.identifiers.details.detailmodal.you")}
                    </span>
                  </div>
                )
              }
            />
          );
        })}
        <p className="bottom-text">{bottomText}</p>
      </CardDetailsBlock>
    </>
  );
};

export { List };
