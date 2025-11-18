import React, { useEffect, useRef, useState } from 'react';
import { Card, CardContent, Typography, Box, CircularProgress, Alert, Button, useTheme } from '@mui/material';
import { Refresh } from '@mui/icons-material';
import * as d3 from 'd3';
import { portfolioService } from '../../services/portfolioService';
import { logger } from '../../utils/logger';
import { EmptyState } from '../common/EmptyState';

interface SankeyNode {
  id: string;
  name: string;
  category: 'exchange' | 'asset';
}

interface SankeyLink {
  source: string;
  target: string;
  value: number;
}

interface SankeyFlowProps {
  width?: number;
  height?: number;
}

const SankeyFlow: React.FC<SankeyFlowProps> = ({ width = 1000, height = 600 }) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const theme = useTheme();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [nodes, setNodes] = useState<SankeyNode[]>([]);
  const [links, setLinks] = useState<SankeyLink[]>([]);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const flowData = await portfolioService.getPortfolioFlow();
      
      // Transform data for Sankey diagram
      const transformedNodes: SankeyNode[] = [];
      const transformedLinks: SankeyLink[] = [];
      
      // Add exchange nodes
      if (flowData.exchanges) {
        flowData.exchanges.forEach((exchange: any) => {
          transformedNodes.push({
            id: `exchange-${exchange.name}`,
            name: exchange.name,
            category: 'exchange',
          });
        });
      }

      // Add asset nodes and links
      if (flowData.assets) {
        flowData.assets.forEach((asset: any) => {
          transformedNodes.push({
            id: `asset-${asset.symbol}`,
            name: asset.symbol,
            category: 'asset',
          });

          if (asset.exchange) {
            transformedLinks.push({
              source: `exchange-${asset.exchange}`,
              target: `asset-${asset.symbol}`,
              value: asset.value_usd || 0,
            });
          }
        });
      }

      setNodes(transformedNodes);
      setLinks(transformedLinks);
    } catch (err: any) {
      logger.error('Error fetching portfolio flow data:', err);
      setError(err?.userMessage || 'Failed to load portfolio flow data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (!svgRef.current || nodes.length === 0 || links.length === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const margin = { top: 20, right: 20, bottom: 20, left: 20 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    // Create Sankey layout (simplified - using manual positioning)
    const exchangeNodes = nodes.filter((n) => n.category === 'exchange');
    const assetNodes = nodes.filter((n) => n.category === 'asset');

    // Position exchange nodes on the left
    const exchangeHeight = innerHeight / exchangeNodes.length;
    exchangeNodes.forEach((node, i) => {
      (node as any).x = margin.left;
      (node as any).y = margin.top + i * exchangeHeight + exchangeHeight / 2;
      (node as any).width = 80;
      (node as any).height = exchangeHeight * 0.8;
    });

    // Position asset nodes on the right
    const assetHeight = innerHeight / assetNodes.length;
    assetNodes.forEach((node, i) => {
      (node as any).x = margin.left + innerWidth - 80;
      (node as any).y = margin.top + i * assetHeight + assetHeight / 2;
      (node as any).width = 80;
      (node as any).height = assetHeight * 0.8;
    });

    // Create scales for link colors
    const colorScale = d3.scaleOrdinal(d3.schemeCategory10);

    // Draw links
    const link = svg
      .append('g')
      .selectAll('path')
      .data(links)
      .enter()
      .append('path')
      .attr('d', (d: any) => {
        const sourceNode = nodes.find((n) => n.id === d.source) as any;
        const targetNode = nodes.find((n) => n.id === d.target) as any;
        if (!sourceNode || !targetNode) return '';

        const x0 = sourceNode.x + sourceNode.width;
        const y0 = sourceNode.y;
        const x1 = targetNode.x;
        const y1 = targetNode.y;

        const curvature = 0.5;
        const xc = (x0 + x1) / 2;
        const yc = (y0 + y1) / 2;

        return `M ${x0} ${y0} C ${xc + (x1 - x0) * curvature} ${y0} ${xc + (x1 - x0) * curvature} ${y1} ${x1} ${y1}`;
      })
      .attr('fill', 'none')
      .attr('stroke', (d: any) => colorScale(d.source))
      .attr('stroke-width', (d: any) => Math.max(1, Math.sqrt(d.value / 1000)))
      .attr('opacity', 0.4)
      .on('mouseover', function (event, d: any) {
        d3.select(this).attr('opacity', 0.8).attr('stroke-width', (d: any) => Math.max(2, Math.sqrt(d.value / 1000) * 1.5));
      })
      .on('mouseout', function (event, d: any) {
        d3.select(this).attr('opacity', 0.4).attr('stroke-width', (d: any) => Math.max(1, Math.sqrt(d.value / 1000)));
      });

    // Draw nodes
    const nodeGroup = svg
      .append('g')
      .selectAll('g')
      .data(nodes)
      .enter()
      .append('g');

    nodeGroup
      .append('rect')
      .attr('x', (d: any) => d.x)
      .attr('y', (d: any) => d.y - d.height / 2)
      .attr('width', (d: any) => d.width)
      .attr('height', (d: any) => d.height)
      .attr('fill', (d: any) => (d.category === 'exchange' ? theme.palette.primary.main : theme.palette.secondary.main))
      .attr('stroke', theme.palette.divider)
      .attr('stroke-width', 1)
      .attr('rx', 4);

    nodeGroup
      .append('text')
      .attr('x', (d: any) => d.x + d.width / 2)
      .attr('y', (d: any) => d.y)
      .attr('text-anchor', 'middle')
      .attr('dy', '0.35em')
      .attr('fill', theme.palette.text.primary)
      .style('font-size', '12px')
      .style('font-weight', 500)
      .text((d: any) => d.name);

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

    link
      .on('mouseover', function (event, d: any) {
        tooltip
          .style('opacity', 1)
          .html(`<div><strong>Flow</strong></div><div>Value: $${d.value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>`)
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
  }, [nodes, links, width, height, theme]);

  if (loading) {
    return (
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
            <CircularProgress />
          </Box>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent>
          <Alert severity="error" onClose={() => setError(null)} action={<Button onClick={fetchData} startIcon={<Refresh />}>Retry</Button>}>
            {error}
          </Alert>
        </CardContent>
      </Card>
    );
  }

  if (nodes.length === 0 || links.length === 0) {
    return (
      <Card>
        <CardContent>
          <EmptyState type="analytics" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            Portfolio Flow Diagram
          </Typography>
          <Button startIcon={<Refresh />} onClick={fetchData} size="small" variant="outlined">
            Refresh
          </Button>
        </Box>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Value flow from exchanges to assets
        </Typography>
        <Box sx={{ overflow: 'auto', width: '100%' }}>
          <svg ref={svgRef} width={width} height={height} style={{ display: 'block' }} />
        </Box>
        <Box sx={{ mt: 2, display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Box sx={{ width: 20, height: 20, bgcolor: theme.palette.primary.main, borderRadius: 1 }} />
            <Typography variant="caption">Exchange</Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Box sx={{ width: 20, height: 20, bgcolor: theme.palette.secondary.main, borderRadius: 1 }} />
            <Typography variant="caption">Asset</Typography>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};

export default SankeyFlow;














