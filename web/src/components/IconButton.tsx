import type { ReactNode } from "react";

type IconButtonProps = {
  icon: ReactNode;
  label: string;
  onClick?: () => void;
  active?: boolean;
  disabled?: boolean;
  type?: "button" | "submit";
};

export function IconButton({ icon, label, onClick, active, disabled, type = "button" }: IconButtonProps) {
  return (
    <button className={`icon-button ${active ? "is-active" : ""}`} disabled={disabled} onClick={onClick} title={label} type={type}>
      <span>{icon}</span>
      <span>{label}</span>
    </button>
  );
}
