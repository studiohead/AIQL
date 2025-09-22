import React from "react";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode;
  variant?: "primary" | "secondary" | "danger";
  className?: string;
}

const Button = ({
  children,
  variant = "primary",
  className,
  ...props
}: ButtonProps): JSX.Element => {
  const baseClass = "button";
  const variantClass = `button--${variant}`;
  const combinedClassName = [baseClass, variantClass, className]
    .filter(Boolean)
    .join(" ");

  return (
    <button className={combinedClassName} {...props}>
      {children}
    </button>
  );
};

export default Button;
