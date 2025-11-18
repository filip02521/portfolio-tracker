import React from 'react';
import { Link, LinkProps } from 'react-router-dom';
import { useRoutePrefetch } from '../../hooks/usePrefetch';

interface PrefetchLinkProps extends LinkProps {
  to: string;
  children: React.ReactNode;
}

/**
 * Link component with automatic prefetching on hover/focus
 */
export const PrefetchLink: React.FC<PrefetchLinkProps> = ({ to, children, ...props }) => {
  const { prefetch, cancel } = useRoutePrefetch(to, { delay: 200 });

  return (
    <Link
      {...props}
      to={to}
      onMouseEnter={prefetch}
      onFocus={prefetch}
      onMouseLeave={cancel}
      onBlur={cancel}
    >
      {children}
    </Link>
  );
};

