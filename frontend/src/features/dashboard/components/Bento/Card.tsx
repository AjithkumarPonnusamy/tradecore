import React from "react";

interface CardProps {
  children: React.ReactNode;
  className?: string;
  title?: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
}

export function Card({ children, className = "", title, icon, action }: CardProps) {
  return (
    <div
      className={`relative p-6 rounded-2xl overflow-hidden transition-all duration-200 group
        bg-[#18181B]
        border border-[#27272A]
        shadow-sm
        hover:border-[#3F3F46]
        flex flex-col justify-between
        ${className}`}
    >
      {title && (
        <div className="flex items-center justify-between mb-5 relative z-10">
          <div className="flex items-center gap-2.5">
            {icon && (
              <div className="w-7 h-7 rounded-lg bg-[#111113] border border-[#27272A] flex items-center justify-center shrink-0 text-slate-400">
                {icon}
              </div>
            )}
            <h3 className="text-xs font-heading font-semibold text-[#FAFAFA] tracking-tight uppercase">
              {title}
            </h3>
          </div>
          {action && <div>{action}</div>}
        </div>
      )}
      <div className="flex-1 relative z-10">{children}</div>
    </div>
  );
}
