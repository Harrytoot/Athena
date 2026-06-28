"use client";

import { useCallback, useRef } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  type Node,
  type Edge,
  type Connection,
  ReactFlowProvider,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useStrategyStore } from "@/stores/strategy-store";
import { StrategyNode } from "@/components/strategy/StrategyNode";
import { getHandles, type NodeTemplate, validateConnection } from "@/components/strategy/types";
import NodeLibrary from "@/components/strategy/NodeLibrary";
import InspectorPanel from "@/components/strategy/InspectorPanel";

const nodeTypes = { strategyNode: StrategyNode };

const defaultEdgeOptions = {
  style: { stroke: "#2A2E39", strokeWidth: 1.5 },
  animated: false,
  type: "smoothstep" as const,
};

function StrategyFlow() {
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const nodes = useStrategyStore((s) => s.nodes);
  const edges = useStrategyStore((s) => s.edges);
  const onNodesChange = useStrategyStore((s) => s.onNodesChange);
  const onEdgesChange = useStrategyStore((s) => s.onEdgesChange);
  const onConnect = useStrategyStore((s) => s.onConnect);
  const addNode = useStrategyStore((s) => s.addNode);
  const selectNode = useStrategyStore((s) => s.selectNode);

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();
      const raw = event.dataTransfer.getData("application/reactflow-template");
      if (!raw) return;
      const template: NodeTemplate = JSON.parse(raw);
      const bounds = reactFlowWrapper.current?.getBoundingClientRect();
      if (!bounds) return;
      const position = {
        x: event.clientX - bounds.left - 80,
        y: event.clientY - bounds.top - 20,
      };
      addNode(template.category, template.type, template.label, template.sublabel, template.defaultData);
    },
    [addNode]
  );

  const handleNodeClick = useCallback(
    (_event: React.MouseEvent, node: Node) => {
      selectNode(node.id);
    },
    [selectNode]
  );

  const handlePaneClick = useCallback(() => {
    selectNode(null);
  }, [selectNode]);

  const handleConnect = useCallback(
    (connection: Connection) => {
      onConnect(connection);
    },
    [onConnect]
  );

  const isValidConnection = useCallback(
    (connection: Connection | Edge) => {
      const sourceHandle = connection.sourceHandle ?? null;
      const targetHandle = connection.targetHandle ?? null;
      if (connection.source === connection.target) return false;
      return validateConnection(sourceHandle, targetHandle);
    },
    []
  );

  return (
    <div className="flex h-full flex-1">
      <NodeLibrary />
      <div ref={reactFlowWrapper} className="flex-1">
        <ReactFlow
          nodes={nodes as Node[]}
          edges={edges}
          onNodesChange={onNodesChange as never}
          onEdgesChange={onEdgesChange}
          onConnect={handleConnect}
          isValidConnection={isValidConnection}
          onNodeClick={handleNodeClick}
          onPaneClick={handlePaneClick}
          onDragOver={onDragOver}
          onDrop={onDrop}
          nodeTypes={nodeTypes}
          defaultEdgeOptions={defaultEdgeOptions}
          fitView
          fitViewOptions={{ padding: 0.3 }}
          onlyRenderVisibleElements
          proOptions={{ hideAttribution: true }}
          style={{ background: "#0B0E14" }}
          connectionLineStyle={{ stroke: "#00B8D9", strokeWidth: 1.5 }}
        >
          <Background
            gap={20}
            size={1}
            color="#2A2E39"
          />
          <Controls
            className="!bg-card !border-border !rounded-lg !shadow-lg [&>button]:!bg-card [&>button]:!text-muted-foreground [&>button]:!border-border [&>button:hover]:!bg-secondary"
          />
        </ReactFlow>
      </div>
      <InspectorPanel />
    </div>
  );
}

export default function StrategyPage() {
  return (
    <div className="h-full">
      <ReactFlowProvider>
        <StrategyFlow />
      </ReactFlowProvider>
    </div>
  );
}
