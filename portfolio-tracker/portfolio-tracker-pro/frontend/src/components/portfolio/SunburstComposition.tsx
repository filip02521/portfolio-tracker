import React, { useEffect, useRef, useMemo } from 'react';
import * as d3 from 'd3';
import { Box, Typography, Card, CardContent, Tooltip, useTheme } from '@mui/material';
import { Asset } from '../../services/portfolioService';
import { EmptyState } from '../common/EmptyState';

interface SunburstNode extends d3.HierarchyNode<any> {
  x0?: number;
  y0?: number;
  x1?: number;
  y1?: number;
  current?: SunburstNode;
  target?: SunburstNode;
}

interface SunburstCompositionProps {
  assets: Asset[];
  width?: number;
  height?: number;
  onSegmentClick?: (path: string[]) => void;
}

const SunburstComposition: React.FC<SunburstCompositionProps> = ({
  assets,
  width = 600,
  height = 600,
  onSegmentClick,
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const theme = useTheme();

  const hierarchyData = useMemo(() => {
    if (!assets || assets.length === 0) return null;

    // Group by exchange, then by asset
    const exchangeMap = new Map<string, Map<string, Asset>>();
    
    assets.forEach((asset) => {
      if (!exchangeMap.has(asset.exchange)) {
        exchangeMap.set(asset.exchange, new Map());
      }
      const assetMap = exchangeMap.get(asset.exchange)!;
      if (!assetMap.has(asset.symbol)) {
        assetMap.set(asset.symbol, asset);
      } else {
        // Sum values if same symbol on same exchange
        const existing = assetMap.get(asset.symbol)!;
        existing.value_usd += asset.value_usd;
        existing.amount += asset.amount;
      }
    });

    // Convert to hierarchical structure
    const children: any[] = [];
    exchangeMap.forEach((assetMap, exchange) => {
      const exchangeChildren: any[] = [];
      assetMap.forEach((asset) => {
        exchangeChildren.push({
          name: asset.symbol,
          value: asset.value_usd,
          asset: asset,
        });
      });
      children.push({
        name: exchange,
        children: exchangeChildren,
      });
    });

    return {
      name: 'Portfolio',
      children: children,
    };
  }, [assets]);

  useEffect(() => {
    if (!hierarchyData || !svgRef.current) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const radius = Math.min(width, height) / 2 - 10;
    const g = svg
      .append('g')
      .attr('transform', `translate(${width / 2},${height / 2})`);

    const partition = d3.partition().size([2 * Math.PI, radius]);

    const root = d3
      .hierarchy(hierarchyData)
      .sum((d: any) => d.value || 0)
      .sort((a, b) => (b.value || 0) - (a.value || 0));

    partition(root as any);

    // Color scales
    const exchangeColor = d3.scaleOrdinal(d3.schemeCategory10);
    const assetColor = (d: any) => {
      if (d.depth === 0) return theme.palette.background.paper;
      if (d.depth === 1) return exchangeColor(d.data.name);
      // For assets, use a lighter shade of parent exchange color
      const parentColor = exchangeColor(d.parent?.data?.name || '');
      return d3.color(parentColor)?.brighter(0.5).toString() || theme.palette.text.secondary;
    };

    const arc = d3
      .arc<SunburstNode>()
      .startAngle((d) => d.x0 || 0)
      .endAngle((d) => d.x1 || 0)
      .innerRadius((d) => d.y0 || 0)
      .outerRadius((d) => d.y1 || 0);

    const path = g
      .selectAll('path')
      .data(root.descendants().filter((d) => d.depth > 0))
      .enter()
      .append('path')
      .attr('fill', (d: any) => assetColor(d))
      .attr('stroke', theme.palette.divider)
      .attr('stroke-width', 1)
      .attr('d', arc as any)
      .style('cursor', 'pointer')
      .on('click', (event, d: any) => {
        const path = [];
        let current = d;
        while (current && current.depth > 0) {
          path.unshift(current.data.name);
          current = current.parent as any;
        }
        if (onSegmentClick) {
          onSegmentClick(path);
        }
      })
      .on('mouseover', function (event, d: any) {
        d3.select(this).attr('stroke-width', 2);
      })
      .on('mouseout', function (event, d: any) {
        d3.select(this).attr('stroke-width', 1);
      });

    // Add labels for larger segments
    const text = g
      .selectAll('text')
      .data(
        root.descendants().filter((d: any) => {
          const angle = (d.x1 || 0) - (d.x0 || 0);
          const radius = (d.y1 || 0) - (d.y0 || 0);
          return angle > 0.1 && radius > 20; // Only show labels for large enough segments
        })
      )
      .enter()
      .append('text')
      .attr('transform', (d: any) => {
        const x = ((d.x0 || 0) + (d.x1 || 0)) / 2;
        const y = ((d.y0 || 0) + (d.y1 || 0)) / 2;
        return `rotate(${(x * 180) / Math.PI - 90}) translate(${y},0) rotate(${x >= Math.PI ? 180 : 0})`;
      })
      .attr('dy', '0.35em')
      .attr('text-anchor', (d: any) => (d.x >= Math.PI ? 'end' : 'start'))
      .attr('fill', theme.palette.text.primary)
      .style('font-size', (d: any) => {
        const radius = (d.y1 || 0) - (d.y0 || 0);
        return `${Math.min(12, radius / 8)}px`;
      })
      .style('font-weight', (d: any) => (d.depth === 1 ? 600 : 400))
      .text((d: any) => {
        const angle = (d.x1 || 0) - (d.x0 || 0);
        const radius = (d.y1 || 0) - (d.y0 || 0);
        if (angle > 0.1 && radius > 30) {
          return d.data.name;
        }
        return '';
      });

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

    path
      .on('mouseover', function (event, d: any) {
        const path = [];
        let current = d;
        while (current && current.depth > 0) {
          path.unshift(current.data.name);
          current = current.parent as any;
        }
        const value = d.value || 0;
        const percentage = root.value ? ((value / root.value) * 100).toFixed(2) : '0.00';

        tooltip
          .style('opacity', 1)
          .html(`
            <div><strong>${path.join(' → ')}</strong></div>
            <div>Value: $${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
            <div>Percentage: ${percentage}%</div>
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
  }, [hierarchyData, width, height, theme, onSegmentClick]);

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
          Portfolio Composition (Sunburst)
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Hierarchical view: Exchange → Asset
        </Typography>
        <Box sx={{ overflow: 'auto', width: '100%', display: 'flex', justifyContent: 'center' }}>
          <svg ref={svgRef} width={width} height={height} style={{ display: 'block' }} />
        </Box>
      </CardContent>
    </Card>
  );
};

export default SunburstComposition;

