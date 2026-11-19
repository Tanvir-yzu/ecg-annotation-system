// Colour per label, used for shaded regions in the viewer and chips in the list.
export const LABEL_COLORS = {
  Normal: "#2e7d32",
  Tachycardia: "#d32f2f",
  Bradycardia: "#1565c0",
  Irregular: "#ef6c00",
  Pause: "#6a1b9a",
  AF: "#c2185b",
  PVC: "#00838f",
  APC: "#5d4037",
  Noise: "#757575",
  Other: "#455a64",
};

export const colorFor = (label) => LABEL_COLORS[label] || "#455a64";
