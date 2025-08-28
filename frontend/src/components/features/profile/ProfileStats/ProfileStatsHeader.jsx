import { Title } from "../../../common/UI/UI";

export default function ProfileStatsHeader({ username }) {
  return <Title>📊 Stats for: {username || "—"}</Title>;
}
