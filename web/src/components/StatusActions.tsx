import { Camera, Clock, Coffee, Moon, Sofa, Trees } from "lucide-react";
import type { ReactNode } from "react";
import { IconButton } from "./IconButton";
import type { UserStatus } from "../types";

const actions: Array<{ status: UserStatus; label: string; icon: ReactNode }> = [
  { status: "tired", label: "我累了", icon: <Sofa size={18} /> },
  { status: "photo", label: "想拍照", icon: <Camera size={18} /> },
  { status: "food", label: "想吃东西", icon: <Coffee size={18} /> },
  { status: "short_time", label: "时间不够", icon: <Clock size={18} /> },
  { status: "quiet", label: "安静路线", icon: <Moon size={18} /> },
  { status: "normal", label: "恢复默认", icon: <Trees size={18} /> }
];

export function StatusActions({
  value,
  onChange,
  disabled
}: {
  value: UserStatus;
  onChange: (status: UserStatus) => void;
  disabled?: boolean;
}) {
  return (
    <div className="status-grid">
      {actions.map((action) => (
        <IconButton
          active={value === action.status}
          disabled={disabled}
          icon={action.icon}
          key={action.status}
          label={action.label}
          onClick={() => onChange(action.status)}
        />
      ))}
    </div>
  );
}
