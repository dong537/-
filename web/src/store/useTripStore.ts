import { create } from "zustand";
import type { CompanionResponse, ExportResponse, FrameAsset, MediaAsset, RoutePlan, TripDetail, TripEvent, UserStatus } from "../types";

type TripStore = {
  tripId?: string;
  destination: string;
  durationMinutes: number;
  preferences: string[];
  route?: RoutePlan;
  media?: MediaAsset;
  frames: FrameAsset[];
  companion?: CompanionResponse;
  exportResult?: ExportResponse;
  events: TripEvent[];
  userStatus: UserStatus;
  setTripInput: (payload: { destination: string; durationMinutes: number; preferences: string[] }) => void;
  setTripId: (tripId: string) => void;
  setRoute: (route: RoutePlan) => void;
  setMedia: (media: MediaAsset) => void;
  setFrames: (frames: FrameAsset[]) => void;
  updateFrame: (frame: FrameAsset) => void;
  setCompanion: (response: CompanionResponse) => void;
  setExportResult: (response: ExportResponse) => void;
  setEvents: (events: TripEvent[]) => void;
  setUserStatus: (status: UserStatus) => void;
  hydrateFromDetail: (detail: TripDetail) => void;
  reset: () => void;
};

const initialState = {
  tripId: undefined,
  destination: "杭州西湖附近",
  durationMinutes: 120,
  preferences: ["风景", "拍视频", "轻松"],
  route: undefined,
  media: undefined,
  frames: [],
  companion: undefined,
  exportResult: undefined,
  events: [],
  userStatus: "normal" as UserStatus
};

export const useTripStore = create<TripStore>((set) => ({
  ...initialState,
  setTripInput: (payload) =>
    set({
      destination: payload.destination,
      durationMinutes: payload.durationMinutes,
      preferences: payload.preferences
    }),
  setTripId: (tripId) => set({ tripId }),
  setRoute: (route) => set({ route }),
  setMedia: (media) => set({ media }),
  setFrames: (frames) => set({ frames }),
  updateFrame: (frame) =>
    set((state) => ({
      frames: state.frames.map((item) => (item.frame_id === frame.frame_id ? frame : item))
    })),
  setCompanion: (companion) => set({ companion }),
  setExportResult: (exportResult) => set({ exportResult }),
  setEvents: (events) => set({ events }),
  setUserStatus: (userStatus) => set({ userStatus }),
  hydrateFromDetail: (detail) =>
    set({
      tripId: typeof detail.trip.id === "string" ? detail.trip.id : undefined,
      destination: typeof detail.trip.destination === "string" ? detail.trip.destination : initialState.destination,
      durationMinutes: typeof detail.trip.duration_minutes === "number" ? detail.trip.duration_minutes : initialState.durationMinutes,
      preferences: Array.isArray(detail.trip.preferences) ? detail.trip.preferences.filter((item): item is string => typeof item === "string") : initialState.preferences,
      route: detail.route ?? undefined,
      media: detail.media.at(-1),
      frames: detail.frames,
      exportResult: detail.exports.at(-1),
      events: detail.events,
      companion: undefined,
      userStatus: initialState.userStatus
    }),
  reset: () => set({ ...initialState })
}));
