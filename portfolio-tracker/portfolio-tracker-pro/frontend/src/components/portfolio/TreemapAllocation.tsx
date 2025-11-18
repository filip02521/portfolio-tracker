import React, { useEffect, useRef, useMemo } from 'react';
import * as d3 from 'd3';
import { Box, Typography, Card, CardContent, Tooltip, useTheme } from '@mui/material';
import { Asset } from '../../services/portfolioService';
import { EmptyState } from '../common/EmptyState';

interface TreemapData {
  name: string;
  value: number;
  pnl: number;
  pnl_percent: number;
  exchange: string;
  children?: TreemapData[];
}

interface TreemapAllocationProps {
  assets: Asset[];
  width?: number;
  height?: number;
  onAssetClick?: (asset: Asset) => void;
}

const TreemapAllocation: React.FC<TreemapAllocationProps> = ({
  assets,
  width = 800,
  height = 600,
  onAssetClick,
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const theme = useTheme();

  const treemapData = useMemo(() => {
    if (!assets || assets.length === 0) return null;

    return {
      name: 'portfolio',
      children: assets.map((asset) => ({
        name: asset.symbol,
        value: asset.value_usd,
        pnl: asset.pnl,
        pnl_percent: asset.pnl_percent,
        exchange: asset.exchange,
      })),
    };
  }, [assets]);

  useEffect(() => {
    if (!treemapData || !svgRef.current) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const margin = { top: 10, right: 10, bottom: 10, left: 10 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    // Create treemap layout
    const treemapRoot = d3
      .hierarchy(treemapData)
      .sum((d: any) => d.value)
      .sort((a, b) => (b.value || 0) - (a.value || 0));

    const treemap = d3.treemap<TreemapData>().size([innerWidth, innerHeight]).padding(2);

    treemap(treemapRoot as any);

    const root = svg
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Color scale based on P&L percentage
    const colorScale = d3
      .scaleLinear<string>()
      .domain([-50, 0, 50])
      .range([
        theme.palette.error.main,
        theme.palette.text.secondary,
        theme.palette.success.main,
      ])
      .interpolate(d3.interpolateRgb);

    // Create cells
    const cell = root
      .selectAll('g')
      .data(treemapRoot.leaves())
      .enter()
      .append('g')
      .attr('transform', (d: any) => `translate(${d.x0},${d.y0})`)
      .style('cursor', 'pointer')
      .on('click', (event, d: any) => {
        const asset = assets.find((a) => a.symbol === d.data.name);
        if (asset && onAssetClick) {
          onAssetClick(asset);
        }
      });

    // Draw rectangles
    cell
      .append('rect')
      .attr('width', (d: any) => d.x1 - d.x0)
      .attr('height', (d: any) => d.y1 - d.y0)
      .attr('fill', (d: any) => colorScale(d.data.pnl_percent || 0))
      .attr('stroke', theme.palette.divider)
      .attr('stroke-width', 1)
      .attr('opacity', 0.9)
      .on('mouseover', function (event, d: any) {
        d3.select(this).attr('opacity', 1).attr('stroke-width', 2);
      })
      .on('mouseout', function (event, d: any) {
        d3.select(this).attr('opacity', 0.9).attr('stroke-width', 1);
      });

    // Add text labels
    const text = cell.append('text').attr('x', 5).attr('y', 15).style('font-size', '12px');

    text
      .selectAll('tspan')
      .data((d: any) => {
        const lines = [];
        if ((d.x1 - d.x0) > 60 && (d.y1 - d.y0) > 30) {
          lines.push({ text: d.data.name, dy: '0em' });
          if ((d.x1 - d.x0) > 80 && (d.y1 - d.y0) > 50) {
            const pnlText = d.data.pnl_percent >= 0 ? '+' : '';
            lines.push({
              text: `${pnlText}${d.data.pnl_percent.toFixed(1)}%`,
              dy: '1.2em',
            });
          }
        }
        return lines;
      })
      .enter()
      .append('tspan')
      .attr('x', 5)
      .attr('dy', (d: any) => d.dy)
      .style('fill', theme.palette.text.primary)
      .style('font-weight', (d: any, i: number) => (i === 0 ? 600 : 400))
      .text((d: any) => d.text);

    // Tooltip
    const tooltip = d3
      .select('body')
      .append('div')
      .style('position', 'absolute')
      .style('padding', '8px')
      .style('background', theme.palette.mode === 'dark' ? 'rgba(45, 55, 72, 0.95)' : 'rgba(255, 255, 255, 0.95)')
      .style('border', `1px solid ${theme.palette.divider}`)
      .style('border-radius', '8px')
      .style('pointer-events', 'none')
      .style('opacity', 0)
      .style('z-index', 1000)
      .style('font-size', '12px')
      .style('box-shadow', '0 4px 12px rgba(0,0,0,0.15)');

    cell
      .on('mouseover', function (event, d: any) {
        const [x, y] = d3.pointer(event);
        tooltip
          .style('opacity', 1)
          .html(`
            <div><strong>${d.data.name}</strong></div>
            <div>Value: $${d.data.value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
            <div>P&L: ${d.data.pnl >= 0 ? '+' : ''}$${d.data.pnl.toFixed(2)}</div>
            <div>P&L %: ${d.data.pnl_percent >= 0 ? '+' : ''}${d.data.pnl_percent.toFixed(2)}%</div>
            <div>Exchange: ${d.data.exchange}</div>
          `)
          .style('left', `${event.pageX + 10}px`)
          .style('top', `${event.pageY - 10}px`);
      })
      .on('mousemove', function (event) {
        tooltip.style('left', `${event.pageX + 10}px`).style('top', `${event.pageY - 10}px`);
      })
      .on('mouseout', function () {
        tooltip.style('opacity', 0);
      });

    return () => {
      tooltip.remove();
    };
  }, [treemapData, width, height, theme, assets, onAssetClick]);

  if (!assets || assets.length === 0) {
    return (
      <Card>
        <CardContent>
          <EmptyState type="portfolio" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
          Portfolio Allocation Treemap
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Size = Value, Color = P&L %
        </Typography>
        <Box sx={{ overflow: 'auto', width: '100%' }}>
          <svg ref={svgRef} width={width} height={height} style={{ display: 'block' }} />
        </Box>
        <Box sx={{ mt: 2, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Box
              sx={{
                width: 16,
                height: 16,
                bgcolor: theme.palette.error.main,
                borderRadius: 1,
              }}
            />
            <Typography variant="caption">Negative P&L</Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Box
              sx={{
                width: 16,
                height: 16,
                bgcolor: theme.palette.success.main,
                borderRadius: 1,
              }}
            />
            <Typography variant="caption">Positive P&L</Typography>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};

export default TreemapAllocation;

