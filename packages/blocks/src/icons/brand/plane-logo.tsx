/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import * as React from "react";

export type PlaneLogoProps = React.ComponentPropsWithoutRef<"svg">;

// Scholrithm mark (source: /branding/scholrithm-mark.svg). Name kept so upstream call sites merge cleanly.
export function PlaneLogo({ width = "37", height = "47", className }: PlaneLogoProps) {
  // unique per instance: a shared id breaks when the first instance sits in a display:none subtree
  const gradientId = `scholrithm-mark-${React.useId().replace(/:/g, "")}`;
  return (
    <svg
      width={width}
      height={height}
      viewBox="13 6 186 234"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden="true"
    >
      <defs>
        <linearGradient id={gradientId} x1="0" y1="8" x2="0" y2="238" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#2DE4FF" />
          <stop offset="0.16" stopColor="#16A4FC" />
          <stop offset="0.36" stopColor="#0A5AE6" />
          <stop offset="0.55" stopColor="#0536C4" />
          <stop offset="0.74" stopColor="#0433B8" />
          <stop offset="0.9" stopColor="#0B6DEE" />
          <stop offset="1" stopColor="#1C9CFD" />
        </linearGradient>
      </defs>
      <g fill={`url(#${gradientId})`} stroke={`url(#${gradientId})`} strokeWidth="7" strokeLinejoin="round">
        <path d="M106 11 L193 58 L169 72 L106 45 L50 78 L50 109 Q72 130 90 142 Q97 147 101 150 Q90 149 81 146 Q60 139 21 120 L18 64 Z" />
        <path d="M81 95 L106 81 L190 121 L194 178 L106 235 L18 186 L42 171 L105 203 L163 169 L163 138 L122 103 L107 109 Z" />
      </g>
      <circle cx="106" cy="152" r="6.8" fill={`url(#${gradientId})`} />
      <path d="M94 105.5 L107 112 L121 105 L121 116.5 L107 123 L94 116.5 Z" fill="#0747D4" />
      <path d="M108 97 L121.5 103" stroke="#FFFFFF" strokeWidth="1.6" strokeLinecap="round" fill="none" />
      <path
        d="M91.5 103.6 L107 111.2 L122.8 103.6"
        stroke="#FFFFFF"
        strokeWidth="1.7"
        strokeLinejoin="round"
        strokeLinecap="round"
        fill="none"
      />
    </svg>
  );
}
