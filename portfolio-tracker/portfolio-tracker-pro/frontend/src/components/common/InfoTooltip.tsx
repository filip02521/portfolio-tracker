import React from 'react';
import { Tooltip, TooltipProps } from '@mui/material';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import { IconButton } from '@mui/material';

export interface InfoTooltipProps extends Omit<TooltipProps, 'children'> {
  children?: React.ReactNode;
  iconSize?: 'small' | 'medium' | 'large';
  iconColor?: 'default' | 'primary' | 'secondary' | 'action' | 'disabled' | 'error' | 'inherit';
}

export const InfoTooltip: React.FC<InfoTooltipProps> = ({
  title,
  iconSize = 'small',
  iconColor = 'action',
  placement = 'top',
  arrow = true,
  ...props
}) => {
  return (
    <Tooltip title={title} placement={placement} arrow={arrow} {...props}>
      <IconButton size="small" sx={{ p: 0.5, color: `${iconColor}.main` }}>
        <InfoOutlinedIcon fontSize={iconSize} />
      </IconButton>
    </Tooltip>
  );
};

