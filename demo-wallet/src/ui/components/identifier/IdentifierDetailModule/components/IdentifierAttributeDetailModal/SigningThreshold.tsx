import { i18n } from "../../../../../../i18n";
import { CardDetailsBlock, CardDetailsItem } from "../../../../card/CardDetails";
import { ListHeader } from "../../../../ListHeader";
import { SigningThresholdProps } from "./IdentifierAttributeDetailModal.types";

export const SigningThreshold = ({ data }: SigningThresholdProps) => {
  return (
    <>
      <ListHeader
        title={i18n.t(
          "tabs.identifiers.details.detailmodal.signingthreshold.threshold.title"
        )}
      />
      <CardDetailsBlock>
        <CardDetailsItem
          info={i18n.t(
            "tabs.identifiers.details.detailmodal.signingthreshold.threshold.text",
            {
              members: data.members?.length || 0,
              threshold: data.kt,
            }
          )}
        />
      </CardDetailsBlock>
    </>
  );
};
