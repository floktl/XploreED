import React from "react";
import { User } from "lucide-react";
import { Title } from "../UI/UI";
import Badge from "../UI/Badge";

export default function ProfileHeader({ username, darkMode }) {
  return (
    <Title>
      <div className="flex items-center gap-2">
        <User className="w-6 h-6" />
        <span>Profile {username && `(${username})`}</span>
        <Badge type="default">Student</Badge>
      </div>
    </Title>
  );
}
