/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import * as React from "react";
import { PlaneLogo } from "./plane-logo";

export type PlaneLockupProps = React.ComponentPropsWithoutRef<"svg">;

// Scholrithm lockup: mark + wordmark. Single colour (currentColor) like the original, so it stays
// legible on light, dark and brand-coloured surfaces. Name kept so upstream call sites merge cleanly.
export function PlaneLockup({ width = "253", height = "53", className, color = "currentColor" }: PlaneLockupProps) {
  return (
    <svg
      width={width}
      height={height}
      viewBox="0 0 253 53"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      role="img"
      aria-label="Scholrithm"
    >
      <PlaneLogo width={42} height={53} color={color} />
      {/* textLength pins the wordmark width whatever font the app inherits */}
      <text
        x="54"
        y="37"
        fill={color}
        fontFamily="inherit"
        fontSize="30"
        fontWeight="800"
        textLength="197"
        lengthAdjust="spacingAndGlyphs"
      >
        SCHOLRITHM
      </text>
    </svg>
  );
}
