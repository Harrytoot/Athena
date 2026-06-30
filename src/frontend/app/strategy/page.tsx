"use client";

import { useCallback, useRef, useState, useEffect } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  type Node,
  type Edge,
  type Connection,
  ReactFlowProvider,
  BackgroundVariant,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useStrategyStore } from "@/stores/strategy-store";
import { StrategyNode } from "@/components/strategy/StrategyNode";
import NodeLibrary from "@/components/strategy/NodeLibrary";
import InspectorPanel from "@/components/strategy/InspectorPanel";
import {
  createStrategy,
  deleteStrategy as deleteStrategyApi,
  getStrategies,
  getStrategy as getStrategyApi,
  updateStrategy,
  type StrategyDTO,
} from "@/lib/strategy-api";
import type { StrategyNodeData } from "@/stores/strategy-store";
import type { NodeTemplate } from "@/components/strategy/types";
import { validateConnection } from "@/components/strategy/types";
import { cn } from "@/lib/utils";

const nodeTypes = { strategyNode: StrategyNode };

const defaultEdgeOptions = {
  style: { stroke: "#3B4252", strokeWidth: 1.5 },
  animated: true,
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
  const setNodes = useStrategyStore((s) => s.setNodes);
  const setEdges = useStrategyStore((s) => s.setEdges);

  const [strategies, setStrategies] = useState<StrategyDTO[]>([]);
  const [activeStrategyId, setActiveStrategyId] = useState<string | null>(null);
  const [activeName, setActiveName] = useState("");
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [saveName, setSaveName] = useState("");
  const [saveCategory, setSaveCategory] = useState("custom");
  const [showNodeLib, setShowNodeLib] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const refreshList = useCallback(async () => {
    try {
      const list = await getStrategies();
      setStrategies(list);
    } catch {}
  }, []);

  useEffect(() => { refreshList(); }, [refreshList]);

  const handleLoadStrategy = async (id: string) => {
    try {
      const s = await getStrategyApi(id);
      setNodes(s.nodes as unknown as Node<StrategyNodeData>[]);
      setEdges(s.edges as Edge[]);
      setActiveStrategyId(s.id);
      setActiveName(s.name);
    } catch {}
  };

  const handleNew = () => {
    setNodes([]); setEdges([]);
    setActiveStrategyId(null); setActiveName("");
  };

  const handleSave = async () => {
    try {
      const _nodes = nodes as any[];
      const _edges = edges as any[];
      if (activeStrategyId) {
        await updateStrategy(activeStrategyId, { nodes: _nodes, edges: _edges });
      } else {
        const created = await createStrategy({
          name: saveName || "未命名策略",
          description: "",
          category: saveCategory,
          nodes: _nodes, edges: _edges,
        });
        setActiveStrategyId(created.id);
        setActiveName(created.name);
      }
      setShowSaveDialog(false);
      await refreshList();
    } catch {}
  };

  const handleSubmitBacktest = async () => {
    setSubmitting(true);
    try {
      const { runBacktest } = await import("@/lib/backtest-api");
      await runBacktest("000001", 120);
    } catch {}
    setTimeout(() => setSubmitting(false), 1500);
  };

  const handleDelete = async () => {
    if (!activeStrategyId) return;
    try {
      await deleteStrategyApi(activeStrategyId);
      handleNew();
      await refreshList();
    } catch {}
  };

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
      const position = { x: event.clientX - bounds.left - 80, y: event.clientY - bounds.top - 20 };
      addNode(template.category, template.type, template.label, template.sublabel, template.defaultData);
    },
    [addNode]
  );

  const handleNodeClick = useCallback((_event: React.MouseEvent, node: Node) => { selectNode(node.id); }, [selectNode]);
  const handlePaneClick = useCallback(() => { selectNode(null); }, [selectNode]);

  const handleConnect = useCallback((connection: Connection) => { onConnect(connection); }, [onConnect]);

  const isValidConnection = useCallback((connection: Connection | Edge) => {
    if (connection.source === connection.target) return false;
    return validateConnection(connection.sourceHandle ?? null, connection.targetHandle ?? null);
  }, []);

  return (
    <div className="flex h-full flex-col">
      {/* Toolbar */}
      <div className="flex items-center gap-2 border-b border-divider bg-card/50 px-3 py-1.5 shrink-0">
        <button onClick={() => setShowNodeLib(!showNodeLib)} className={cn("text-[10px] px-2 py-0.5 rounded border border-border text-muted-foreground hover:text-foreground transition-colors", showNodeLib && "bg-primary/15 border-primary/30 text-primary")}>
          Nodes
        </button>
        <span className="text-[11px] font-semibold text-foreground/80">{activeName || "未命名策略"}</span>

        <div className="flex items-center gap-1 ml-auto">
          <button onClick={handleNew} className="text-[10px] px-2 py-0.5 rounded border border-border text-muted-foreground hover:text-foreground">
            新建
          </button>
          <button onClick={() => { setSaveName(activeName || ""); setShowSaveDialog(true); }} className="text-[10px] px-2 py-0.5 rounded bg-primary/20 text-primary hover:bg-primary/30">
            保存拓扑
          </button>
          <button onClick={handleSubmitBacktest} disabled={submitting || nodes.length === 0} className="text-[10px] px-2 py-0.5 rounded bg-up/20 text-up hover:bg-up/30 disabled:opacity-30">
            {submitting ? "提交中..." : "提交异步回测"}
          </button>
          {activeStrategyId && (
            <button onClick={handleDelete} className="text-[10px] px-2 py-0.5 rounded text-muted-foreground hover:text-down">
              删除
            </button>
          )}
        </div>
      </div>

      {/* Save Dialog */}
      {showSaveDialog && (
        <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="rounded-lg border border-border bg-card p-5 shadow-xl w-80">
            <h3 className="text-sm font-semibold text-foreground mb-3">保存策略拓扑</h3>
            <input
              type="text" value={saveName}
              onChange={(e) => setSaveName(e.target.value)}
              className="w-full rounded border border-border bg-background px-2 py-1.5 text-xs text-foreground mb-3"
              placeholder="策略名称"
            />
            <div className="flex justify-end gap-2">
              <button onClick={() => setShowSaveDialog(false)} className="rounded bg-secondary px-3 py-1 text-[11px] text-foreground">取消</button>
              <button onClick={handleSave} className="rounded bg-primary px-3 py-1 text-[11px] text-primary-foreground">保存</button>
            </div>
          </div>
        </div>
      )}

      {/* Main Canvas */}
      <div className="flex flex-1 min-h-0">
        {showNodeLib && <NodeLibrary />}
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
            style={{ background: "#080A10" }}
            connectionLineStyle={{ stroke: "#00B8D9", strokeWidth: 1.5 }}
            snapToGrid
            snapGrid={[20, 20]}
          >
            <Background variant={BackgroundVariant.Dots} gap={20} size={0.5} color="#232838" />
            <Controls className="!bg-card !border-border !rounded-lg !shadow-lg [&>button]:!bg-card [&>button]:!text-muted-foreground [&>button]:!border-divider [&>button:hover]:!bg-secondary" />
            <MiniMap
              nodeStrokeColor="#3B4252"
              nodeColor="#121621"
              maskColor="rgba(8, 10, 16, 0.7)"
              className="!bg-card !border-border !rounded-lg"
            />
          </ReactFlow>
        </div>
        <InspectorPanel />
      </div>
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
