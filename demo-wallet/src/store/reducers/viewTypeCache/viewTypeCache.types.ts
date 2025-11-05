import { CardListViewType } from "../../../ui/components/card/SwitchCardView";

interface ViewType {
  viewType: CardListViewType | null;
  favouriteIndex: number;
}

interface ViewTypeCacheProps {
  identifier: ViewType;
  credential: ViewType;
}
export type { ViewTypeCacheProps };
