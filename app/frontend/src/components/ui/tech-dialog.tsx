import React from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './dialog';
import { X, Code, Database, Cloud, Cpu, Brain, Sparkles } from 'lucide-react';

interface TechDialogProps {
  isOpen: boolean;
  onClose: () => void;
}

const TechDialog: React.FC<TechDialogProps> = ({ isOpen, onClose }) => {
  console.log('🎭 TechDialog render - isOpen:', isOpen);
  
  const technologies = [
    {
      category: "Frontend",
      icon: <Code className="h-6 w-6" />,
      items: [
        { name: "React 18", description: "Bibliothèque UI moderne avec hooks" },
        { name: "TypeScript", description: "Typage statique pour JavaScript" },
        { name: "Tailwind CSS", description: "Framework CSS utility-first" },
        { name: "Vite", description: "Outil de build ultra-rapide" },
        { name: "Lucide React", description: "Icônes SVG modulaires" }
      ]
    },
    {
      category: "Backend",
      icon: <Database className="h-6 w-6" />,
      items: [
        { name: "Python 3.12", description: "Langage de programmation principal" },
        { name: "aiohttp", description: "Framework web asynchrone" },
        { name: "Azure Identity", description: "Authentification Azure" },
        { name: "Pydantic", description: "Validation de données" }
      ]
    },
    {
      category: "Intelligence Artificielle",
      icon: <Brain className="h-6 w-6" />,
      items: [
        { name: "Azure OpenAI", description: "Modèles GPT-4o en temps réel" },
        { name: "Embeddings", description: "text-embedding-3-large" },
        { name: "Whisper", description: "Reconnaissance vocale" },
        { name: "TTS", description: "Synthèse vocale" }
      ]
    },
    {
      category: "Recherche & Données",
      icon: <Database className="h-6 w-6" />,
      items: [
        { name: "Azure AI Search", description: "Recherche hybride sémantique" },
        { name: "Vector Search", description: "Recherche vectorielle avancée" },
        { name: "Azure Blob Storage", description: "Stockage de documents" },
        { name: "RAG Architecture", description: "Retrieval-Augmented Generation" }
      ]
    },
    {
      category: "Observabilité",
      icon: <Sparkles className="h-6 w-6" />,
      items: [
        { name: "Azure Monitor", description: "Monitoring et télémétrie" },
        { name: "OpenTelemetry", description: "Tracing distribué" },
        { name: "Application Insights", description: "Analytics et diagnostics" },
        { name: "Live Metrics", description: "Métriques en temps réel" }
      ]
    },
    {
      category: "Infrastructure",
      icon: <Cloud className="h-6 w-6" />,
      items: [
        { name: "Azure Container Apps", description: "Hébergement serverless" },
        { name: "Azure Container Registry", description: "Registry Docker privé" },
        { name: "Bicep", description: "Infrastructure as Code" },
        { name: "Azure Developer CLI", description: "Déploiement automatisé" }
      ]
    }
  ];

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto glass border-white/20">
        <DialogHeader>
          <DialogTitle className="text-2xl text-white font-bold flex items-center gap-2">
            <Sparkles className="h-6 w-6 text-yellow-400" />
            Technologies Utilisées
          </DialogTitle>
        </DialogHeader>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
          {technologies.map((tech, index) => (
            <div key={index} className="glass-card rounded-xl p-4">
              <div className="flex items-center gap-2 mb-4">
                <div className="text-blue-400">{tech.icon}</div>
                <h3 className="text-lg font-semibold text-white">{tech.category}</h3>
              </div>
              
              <div className="space-y-3">
                {tech.items.map((item, itemIndex) => (
                  <div key={itemIndex} className="border-l-2 border-blue-400/30 pl-3">
                    <div className="text-white font-medium">{item.name}</div>
                    <div className="text-white/70 text-sm">{item.description}</div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
        
        <div className="mt-6 glass-card rounded-xl p-4 text-center">
          <div className="flex items-center justify-center gap-2 mb-2">
            <Cpu className="h-5 w-5 text-green-400" />
            <span className="text-white font-medium">Architecture</span>
          </div>
          <p className="text-white/80 text-sm">
            Application moderne cloud-native avec architecture RAG (Retrieval-Augmented Generation),
            observabilité complète et déploiement automatisé sur Azure
          </p>
        </div>
        
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 rounded-full glass-card hover:bg-white/10 transition-colors"
        >
          <X className="h-4 w-4 text-white" />
        </button>
      </DialogContent>
    </Dialog>
  );
};

export default TechDialog;