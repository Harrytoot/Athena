"use client";

import { useCallback, useEffect, useRef, useState } from "react";
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
import {
  createStrategy,
  deleteStrategy as deleteStrategyApi,
  getStrategies,
  getStrategy as getStrategyApi,
  getStrategyTemplates,
  updateStrategy,
  type StrategyDTO,
} from "@/lib/strategy-api";
import type { StrategyNodeData } from "@/stores/strategy-store";

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
  const setNodes = useStrategyStore((s) => s.setNodes);
  const setEdges = useStrategyStore((s) => s.setEdges);

  const [strategies, setStrategies] = useState<StrategyDTO[]>([]);
  const [templates, setTemplates] = useState<StrategyDTO[]>([]);
  const [activeStrategyId, setActiveStrategyId] = useState<string | null>(null);
  const [activeName, setActiveName] = useState("");
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [saveName, setSaveName] = useState("");
  const [saveCategory, setSaveCategory] = useState("custom");
  const [saveDesc, setSaveDesc] = useState("");

  const refreshList = useCallback(async () => {
    try {
      const [list, temps] = await Promise.all([getStrategies(), getStrategyTemplates()]);
      setStrategies(list);
      setTemplates(temps);
    } catch {
      // backend not ready
    }
  }, []);

  useEffect(() => {
    refreshList();
  }, [refreshList]);

  const handleLoadStrategy = async (id: string) => {
    try {
      const s = await getStrategyApi(id);
      setNodes(s.nodes as unknown as Node<StrategyNodeData>[]);
      setEdges(s.edges as Edge[]);
      setActiveStrategyId(s.id);
      setActiveName(s.name);
    } catch {}
  };

  const handleLoadTemplate = async (id: string) => {
    try {
      const s = await getStrategyApi(id);
      setNodes(s.nodes as unknown as Node<StrategyNodeData>[]);
      setEdges(s.edges as Edge[]);
      setActiveStrategyId(null);
      setActiveName("");
    } catch {}
  };

  const handleNew = () => {
    setNodes([]);
    setEdges([]);
    setActiveStrategyId(null);
    setActiveName("");
  };

  const handleSave = async () => {
    try {
      // eslint-disable-next-line
      const _nodes = nodes as any[];
      // eslint-disable-next-line
      const _edges = edges as any[];
      if (activeStrategyId) {
        await updateStrategy(activeStrategyId, {
          nodes: _nodes,
          edges: _edges,
        });
      } else {
        const created = await createStrategy({
          name: saveName || "未命名策略",
          description: saveDesc,
          category: saveCategory,
          nodes: _nodes,
          edges: _edges,
        });
        setActiveStrategyId(created.id);
        setActiveName(created.name);
      }
      setShowSaveDialog(false);
      await refreshList();
    } catch {}
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
    <div className="flex h-full flex-col">
      {/* Toolbar */}
      <div className="flex items-center gap-2 border-b border-border bg-card px-4 py-2">
        <span className="text-sm font-semibold text-muted-foreground mr-2">
          {activeName || "未命名策略"}
        </span>

        <select
          className="rounded border border-border bg-secondary px-2 py-1 text-xs text-foreground"
          value=""
          onChange={(e) => {
            if (e.target.value.startsWith("template:")) {
              handleLoadTemplate(e.target.value.slice(9));
            } else if (e.target.value) {
              handleLoadStrategy(e.target.value);
            }
          }}
        >
          <option value="">加载策略...</option>
          {templates.length > 0 && (
            <optgroup label="模板">
              {templates.map((s) => (
                <option key={s.id} value={`template:${s.id}`}>{s.name}</option>
              ))}
            </optgroup>
          )}
          {strategies.length > 0 && (
            <optgroup label="我的策略">
              {strategies.map((s) => (
                <option key={s.id} value={s.id}>{s.name}</option>
              ))}
            </optgroup>
          )}
        </select>

        <button onClick={handleNew} className="rounded bg-secondary px-2 py-1 text-xs text-foreground hover:bg-muted">
          新建
        </button>
        <button
          onClick={() => {
            setSaveName(activeName || "");
            setShowSaveDialog(true);
          }}
          className="rounded bg-primary px-2 py-1 text-xs text-primary-foreground hover:bg-primary/80"
        >
          保存
        </button>
        {activeStrategyId && (
          <button onClick={handleDelete} className="rounded bg-red-500/20 px-2 py-1 text-xs text-red-500 hover:bg-red-500/30">
            删除
          </button>
        )}
        <span className="ml-auto text-xs text-muted-foreground">
          节点: {nodes.length} · 连线: {edges.length}
        </span>
      </div>

      {/* Save Dialog */}
      {showSaveDialog && (
        <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="rounded-lg border border-border bg-card p-6 shadow-xl w-96">
            <h3 className="text-lg font-semibold text-foreground mb-4">保存策略</h3>
            <div className="space-y-3">
              <div>
                <label className="text-xs text-muted-foreground">名称</label>
                <input
                  type="text"
                  value={saveName}
                  onChange={(e) => setSaveName(e.target.value)}
                  className="w-full rounded border border-border bg-secondary px-2 py-1.5 text-sm text-foreground mt-1"
                  placeholder="策略名称"
                />
              </div>
              <div>
                <label className="text-xs text-muted-foreground">分类</label>
                <input
                  type="text"
                  value={saveCategory}
                  onChange={(e) => setSaveCategory(e.target.value)}
                  className="w-full rounded border border-border bg-secondary px-2 py-1.5 text-sm text-foreground mt-1"
                />
              </div>
              <div>
                <label className="text-xs text-muted-foreground">描述</label>
                <textarea
                  value={saveDesc}
                  onChange={(e) => setSaveDesc(e.target.value)}
                  className="w-full rounded border border-border bg-secondary px-2 py-1.5 text-sm text-foreground mt-1"
                  rows={2}
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-4">
              <button onClick={() => setShowSaveDialog(false)} className="rounded bg-secondary px-3 py-1.5 text-sm text-foreground hover:bg-muted">
                取消
              </button>
              <button onClick={handleSave} className="rounded bg-primary px-3 py-1.5 text-sm text-primary-foreground hover:bg-primary/80">
                保存
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Main Canvas */}
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
            <Background gap={20} size={1} color="#2A2E39" />
            <Controls className="!bg-card !border-border !rounded-lg !shadow-lg [&>button]:!bg-card [&>button]:!text-muted-foreground [&>button]:!border-border [&>button:hover]:!bg-secondary" />
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
