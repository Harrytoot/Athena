import { create } from "zustand";
import {
  type Node,
  type Edge,
  type OnNodesChange,
  type OnEdgesChange,
  type OnConnect,
  applyNodeChanges,
  applyEdgeChanges,
  addEdge,
  type Connection,
} from "@xyflow/react";
import type { NodeCategory } from "@/components/strategy/types";
import { getHandles, validateConnection } from "@/components/strategy/types";

export interface StrategyNodeData extends Record<string, unknown> {
  category: NodeCategory;
  label: string;
  sublabel: string;
  properties: Record<string, unknown>;
}

interface StrategyStore {
  nodes: Node<StrategyNodeData>[];
  edges: Edge[];
  selectedNodeId: string | null;

  setNodes: (nodes: Node<StrategyNodeData>[]) => void;
  setEdges: (edges: Edge[]) => void;
  onNodesChange: OnNodesChange<Node<StrategyNodeData>>;
  onEdgesChange: OnEdgesChange;
  onConnect: (connection: Connection) => void;

  addNode: (category: NodeCategory, type: string, label: string, sublabel: string, defaultData: Record<string, unknown>) => void;
  selectNode: (id: string | null) => void;
  updateNodeProperties: (id: string, properties: Record<string, unknown>) => void;
  removeNode: (id: string) => void;
}

let nodeIdCounter = 0;

export const useStrategyStore = create<StrategyStore>((set, get) => ({
  nodes: [],
  edges: [],
  selectedNodeId: null,

  setNodes: (nodes) => set({ nodes }),
  setEdges: (edges) => set({ edges }),

  onNodesChange: (changes) => {
    set({ nodes: applyNodeChanges(changes, get().nodes) as Node<StrategyNodeData>[] });
  },

  onEdgesChange: (changes) => {
    set({ edges: applyEdgeChanges(changes, get().edges) });
  },

  onConnect: (connection: Connection) => {
    const { nodes } = get();
    const sourceNode = nodes.find((n) => n.id === connection.source);
    const targetNode = nodes.find((n) => n.id === connection.target);

    const sourceHandle = connection.sourceHandle ?? null;
    const targetHandle = connection.targetHandle ?? null;

    if (!validateConnection(sourceHandle, targetHandle)) {
      return;
    }

    if (sourceNode && targetNode && sourceNode.id === targetNode.id) {
      return;
    }

    const exists = get().edges.some(
      (e) =>
        e.source === connection.source &&
        e.target === connection.target &&
        e.sourceHandle === connection.sourceHandle &&
        e.targetHandle === connection.targetHandle
    );
    if (exists) return;

    set({ edges: addEdge(connection, get().edges) });
  },

  addNode: (category, type, label, sublabel, defaultData) => {
    nodeIdCounter += 1;
    const id = `node_${nodeIdCounter}`;
    const { nodes } = get();
    const avgX = nodes.length > 0
      ? nodes.reduce((s, n) => s + n.position.x, 0) / nodes.length
      : 250;
    const avgY = nodes.length > 0
      ? nodes.reduce((s, n) => s + n.position.y, 0) / nodes.length
      : 200;

    const newNode: Node<StrategyNodeData> = {
      id,
      type: "strategyNode",
      position: { x: avgX + 30, y: avgY + 30 },
      data: {
        category,
        label,
        sublabel,
        properties: { ...defaultData },
      },
    };

    set({
      nodes: [...nodes, newNode],
      selectedNodeId: id,
    });
  },

  selectNode: (id) => set({ selectedNodeId: id }),

  updateNodeProperties: (id, properties) => {
    set({
      nodes: get().nodes.map((n) =>
        n.id === id
          ? { ...n, data: { ...n.data, properties: { ...n.data.properties, ...properties } } }
          : n
      ),
    });
  },

  removeNode: (id) => {
    set({
      nodes: get().nodes.filter((n) => n.id !== id),
      edges: get().edges.filter((e) => e.source !== id && e.target !== id),
      selectedNodeId: get().selectedNodeId === id ? null : get().selectedNodeId,
    });
  },
}));
