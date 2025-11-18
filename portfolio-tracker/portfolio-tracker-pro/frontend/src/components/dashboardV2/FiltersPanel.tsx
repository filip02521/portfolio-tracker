import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Stack,
  Chip,
  ToggleButtonGroup,
  ToggleButton,
  Switch,
  FormControlLabel,
  Divider,
  Button,
  Tooltip,
} from '@mui/material';
import FilterListIcon from '@mui/icons-material/FilterList';
import RestartAltIcon from '@mui/icons-material/RestartAlt';
import { FiltersState } from './types';
import { dashboardPalette, timeRangeOptions } from '../../theme/dashboardTokens';
import { SectionHeader } from '../common/SectionHeader';

export interface FiltersPanelProps {
  filters: FiltersState;
  onFiltersChange: (filters: Partial<FiltersState>) => void;
  onReset?: () => void;
}

const filterOptions = {
  assetTypes: ['Stocks', 'Crypto', 'Funds', 'Commodities'],
  sectors: ['Technology', 'Finance', 'Healthcare', 'Energy', 'Consumer'],
  regions: ['North America', 'Europe', 'Asia', 'LATAM'],
  tags: ['DeFi', 'AI', 'Blue Chip', 'Growth', 'Dividend'],
};

const toggleSelection = (current: string[], value: string): string[] => {
  return current.includes(value) ? current.filter((item) => item !== value) : [...current, value];
};

export const FiltersPanel: React.FC<FiltersPanelProps> = ({ filters, onFiltersChange, onReset }) => {
  return (
    <Card variant="outlined" sx={{ borderRadius: 2 }}>
      <CardContent sx={{ display: 'flex', flexDirection: 'column', gap: 2.5, p: 3.5 }}>
        <Box sx={{ mb: 1 }}>
          <SectionHeader
            title="Dashboard Filters"
            description="Filter dashboard data by time range, asset type, sector, region, and view mode. Use filters to focus on specific parts of your portfolio."
            tooltip="Filters help you focus on specific aspects of your portfolio. Time range affects historical charts, asset type filters holdings, sector/region filter by classification, and view mode changes how assets are displayed (table/cards/chart)."
            icon={<FilterListIcon />}
          />
        </Box>
        {onReset && (
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 1 }}>
            <Tooltip title="Reset all filters to default values. This clears all selected filters and restores the default dashboard view." arrow>
              <Button
                size="small"
                startIcon={<RestartAltIcon />}
                onClick={onReset}
                sx={{ textTransform: 'none', borderRadius: 2, minHeight: 36 }}
              >
                Reset
              </Button>
            </Tooltip>
          </Box>
        )}

        <Stack spacing={1.5}>
          <Tooltip title="Select the time period for portfolio performance charts and analytics. This affects the equity curve, returns, and historical data displayed throughout the dashboard." arrow>
            <Typography variant="subtitle2" color="text.secondary" sx={{ fontWeight: 600 }}>
              Time Range
            </Typography>
          </Tooltip>
          <ToggleButtonGroup
            exclusive
            size="small"
            value={filters.timeRange}
            onChange={(_, nextValue) => {
              if (nextValue) {
                onFiltersChange({ timeRange: nextValue });
              }
            }}
            sx={{
              backgroundColor: 'action.hover',
              borderRadius: 2.5,
              p: 0.5,
              '.MuiToggleButton-root': {
                border: 'none',
                textTransform: 'none',
                borderRadius: 2.5,
                px: 2,
                py: 0.75,
                minHeight: 36,
                fontWeight: 500,
                '&.Mui-selected': {
                  color: '#fff',
                  backgroundColor: dashboardPalette.primary,
                  fontWeight: 600,
                },
              },
            }}
          >
            {timeRangeOptions.map((option) => (
              <ToggleButton key={option} value={option}>
                {option.toUpperCase()}
              </ToggleButton>
            ))}
          </ToggleButtonGroup>
        </Stack>

        <Divider />

        <Stack spacing={1.5}>
          <Tooltip title="Filter assets by type (Stocks, Crypto, Funds, Commodities). Click chips to toggle filters. Multiple types can be selected." arrow>
            <Typography variant="subtitle2" color="text.secondary" sx={{ fontWeight: 600 }}>
              Asset Type
            </Typography>
          </Tooltip>
          <Stack direction="row" spacing={1} flexWrap="wrap">
            {filterOptions.assetTypes.map((type) => (
              <Tooltip key={type} title={`${filters.assetType.includes(type) ? 'Remove' : 'Add'} ${type} filter`} arrow>
                <Chip
                  label={type}
                  onClick={() => onFiltersChange({ assetType: toggleSelection(filters.assetType, type) })}
                  variant={filters.assetType.includes(type) ? 'filled' : 'outlined'}
                  sx={{ borderRadius: 2, fontWeight: filters.assetType.includes(type) ? 600 : 500, cursor: 'pointer' }}
                />
              </Tooltip>
            ))}
          </Stack>
        </Stack>

        <Stack spacing={1.5}>
          <Tooltip title="Filter assets by sector or industry classification. Useful for analyzing exposure to specific market segments." arrow>
            <Typography variant="subtitle2" color="text.secondary" sx={{ fontWeight: 600 }}>
              Sector / Industry
            </Typography>
          </Tooltip>
          <Stack direction="row" spacing={1} flexWrap="wrap">
            {filterOptions.sectors.map((sector) => (
              <Tooltip key={sector} title={`${filters.sector.includes(sector) ? 'Remove' : 'Add'} ${sector} sector filter`} arrow>
                <Chip
                  label={sector}
                  onClick={() => onFiltersChange({ sector: toggleSelection(filters.sector, sector) })}
                  variant={filters.sector.includes(sector) ? 'filled' : 'outlined'}
                  sx={{ borderRadius: 2, fontWeight: filters.sector.includes(sector) ? 600 : 500, cursor: 'pointer' }}
                />
              </Tooltip>
            ))}
          </Stack>
        </Stack>

        <Stack spacing={1.5}>
          <Tooltip title="Filter assets by geographic region. Useful for analyzing regional exposure and diversification." arrow>
            <Typography variant="subtitle2" color="text.secondary" sx={{ fontWeight: 600 }}>
              Region
            </Typography>
          </Tooltip>
          <Stack direction="row" spacing={1} flexWrap="wrap">
            {filterOptions.regions.map((region) => (
              <Tooltip key={region} title={`${filters.region.includes(region) ? 'Remove' : 'Add'} ${region} region filter`} arrow>
                <Chip
                  label={region}
                  onClick={() => onFiltersChange({ region: toggleSelection(filters.region, region) })}
                  variant={filters.region.includes(region) ? 'filled' : 'outlined'}
                  sx={{ borderRadius: 2, fontWeight: filters.region.includes(region) ? 600 : 500, cursor: 'pointer' }}
                />
              </Tooltip>
            ))}
          </Stack>
        </Stack>

        <Stack spacing={1.5}>
          <Tooltip title="Filter assets by tags (DeFi, AI, Blue Chip, Growth, Dividend). Tags help categorize assets by characteristics or themes." arrow>
            <Typography variant="subtitle2" color="text.secondary" sx={{ fontWeight: 600 }}>
              Tags
            </Typography>
          </Tooltip>
          <Stack direction="row" spacing={1} flexWrap="wrap">
            {filterOptions.tags.map((tag) => (
              <Tooltip key={tag} title={`${filters.tags.includes(tag) ? 'Remove' : 'Add'} ${tag} tag filter`} arrow>
                <Chip
                  label={tag}
                  onClick={() => onFiltersChange({ tags: toggleSelection(filters.tags, tag) })}
                  variant={filters.tags.includes(tag) ? 'filled' : 'outlined'}
                  sx={{ borderRadius: 2, fontWeight: filters.tags.includes(tag) ? 600 : 500, cursor: 'pointer' }}
                />
              </Tooltip>
            ))}
          </Stack>
        </Stack>

        <Divider />

        <Stack spacing={2.5}>
          <Tooltip title="Focus view on stablecoins only. This filters out volatile assets and shows only stable value assets like USDT, USDC, etc." arrow>
            <FormControlLabel
              control={
                <Switch
                  checked={filters.stablecoinsOnly}
                  onChange={(event) => onFiltersChange({ stablecoinsOnly: event.target.checked })}
                />
              }
              label="Stablecoins focus"
              sx={{ cursor: 'help' }}
            />
          </Tooltip>

          <Box>
            <Tooltip title="Change how assets are displayed: Table (detailed list), Cards (visual cards), or Chart (graphical view). Each mode provides different insights." arrow>
              <Typography variant="subtitle2" color="text.secondary" sx={{ fontWeight: 600, mb: 1 }}>
                View Mode
              </Typography>
            </Tooltip>
            <Tooltip title="Table view: Detailed list with all metrics. Cards view: Visual cards with key info. Chart view: Graphical representation of holdings." arrow>
              <ToggleButtonGroup
                exclusive
                value={filters.viewMode}
                onChange={(_, nextValue) => {
                  if (nextValue) {
                    onFiltersChange({ viewMode: nextValue });
                  }
                }}
                sx={{
                  mt: 1,
                  backgroundColor: 'action.hover',
                  borderRadius: 2.5,
                  p: 0.5,
                  '.MuiToggleButton-root': {
                    textTransform: 'none',
                    borderRadius: 2.5,
                    px: 2.5,
                    py: 0.75,
                    minHeight: 36,
                    fontWeight: 500,
                    '&.Mui-selected': {
                      color: '#fff',
                      backgroundColor: dashboardPalette.primary,
                      fontWeight: 600,
                    },
                  },
                }}
              >
                <ToggleButton value="table">Table</ToggleButton>
                <ToggleButton value="cards">Cards</ToggleButton>
                <ToggleButton value="chart">Chart</ToggleButton>
              </ToggleButtonGroup>
            </Tooltip>
          </Box>
        </Stack>
      </CardContent>
    </Card>
  );
};


