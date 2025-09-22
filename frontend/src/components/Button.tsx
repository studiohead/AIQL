import React from "react";
import { Button as MantineButton, ButtonProps as MantineButtonProps } from "@mantine/core";

interface ButtonProps extends Omit<MantineButtonProps, "variant"> {
  children: React.ReactNode;
  variant?: "primary" | "secondary" | "danger";
}

const variantMap: Record<string, MantineButtonProps["variant"]> = {
  primary: "filled",
  secondary: "default",
  danger: "filled",
};

const colorMap: Record<string, string> = {
  primary: "blue",
  secondary: "gray",
  danger: "red",
};

const Button: React.FC<ButtonProps> = ({
  children,
  variant = "primary",
  color,
  ...props
}) => {
  const mantineVariant = variantMap[variant] || "filled";
  const mantineColor = color || colorMap[variant] || "blue";

  return (
    <MantineButton variant={mantineVariant} color={mantineColor} {...props}>
      {children}
    </MantineButton>
  );
};

export default Button;
