import React from "react";

export type LayoutOption = "default" | "minimal" | "custom";

export interface LayoutSwitcherProps {
  option?: LayoutOption;
  children: React.ReactNode;
}

export const LayoutSwitcher: React.FC<LayoutSwitcherProps> = ({ option = "default", children }) => {
  switch (option) {
    case "minimal":
      return <div className="p-2 bg-white text-black">{children}</div>;
    case "custom":
      return <div className="custom-layout">{children}</div>;
    case "default":
    default:
      return <div className="container mx-auto p-8">{children}</div>;
  }
};
