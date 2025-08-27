import React from "react";
import { Title } from "../UI/UI";

export default function ProfileStatsHeader({ username }) {
  return <Title>📊 Stats for: {username || "—"}</Title>;
}
