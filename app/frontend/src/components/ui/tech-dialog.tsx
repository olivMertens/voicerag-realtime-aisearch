import React from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './dialog';
import { X, Code, Database, Cloud, Cpu, Brain, Sparkles } from 'lucide-react';
import { useTranslation } from "react-i18next";

interface TechDialogProps {
  isOpen: boolean;
  onClose: () => void;
}

const TechDialog: React.FC<TechDialogProps> = ({ isOpen, onClose }) => {
  console.log('🎭 TechDialog render - isOpen:', isOpen);
  const { t } = useTranslation();
  
  const technologies = [
    {
      category: t("tech.frontend"),
      icon: <Code className="h-6 w-6" />,
      items: [
        { name: "React 18", description: t("tech.react") },
        { name: "TypeScript", description: t("tech.typescript") },
        { name: "Tailwind CSS", description: t("tech.tailwind") },
        { name: "Vite", description: t("tech.vite") },
        { name: "Lucide React", description: t("tech.lucide") }
      ]
    },
    {
      category: t("tech.backend"),
      icon: <Database className="h-6 w-6" />,
      items: [
        { name: "Python 3.12", description: t("tech.python") },
        { name: "aiohttp", description: t("tech.aiohttp") },
        { name: "Azure Identity", description: t("tech.azureIdentity") },
        { name: "Pydantic", description: t("tech.pydantic") }
      ]
    },
    {
      category: t("tech.ai"),
      icon: <Brain className="h-6 w-6" />,
      items: [
        { name: "Azure OpenAI", description: t("tech.azureOpenAI") },
        { name: "Embeddings", description: "text-embedding-3-large" },
        { name: "Whisper", description: t("tech.whisper") },
        { name: "TTS", description: t("tech.tts") }
      ]
    },
    {
      category: t("tech.searchData"),
      icon: <Database className="h-6 w-6" />,
      items: [
        { name: "Azure AI Search", description: t("tech.azureAISearch") },
        { name: "Vector Search", description: t("tech.vectorSearch") },
        { name: "Azure Blob Storage", description: t("tech.blob") },
        { name: "RAG Architecture", description: "Retrieval-Augmented Generation" }
      ]
    },
    {
      category: t("tech.observability"),
      icon: <Sparkles className="h-6 w-6" />,
      items: [
        { name: "Azure Monitor", description: t("tech.azureMonitor") },
        { name: "OpenTelemetry", description: t("tech.opentelemetry") },
        { name: "Application Insights", description: t("tech.appInsights") },
        { name: "Live Metrics", description: t("tech.liveMetrics") }
      ]
    },
    {
      category: t("tech.infrastructure"),
      icon: <Cloud className="h-6 w-6" />,
      items: [
        { name: "Azure Container Apps", description: t("tech.containerApps") },
        { name: "Azure Container Registry", description: t("tech.acr") },
        { name: "Bicep", description: t("tech.bicep") },
        { name: "Azure Developer CLI", description: t("tech.azd") }
      ]
    }
  ];

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto glass border-white/20">
        <DialogHeader>
          <DialogTitle className="text-2xl text-white font-bold flex items-center gap-2">
            <Sparkles className="h-6 w-6 text-yellow-400" />
            {t("tech.title")}
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
            <span className="text-white font-medium">{t("tech.architecture")}</span>
          </div>
          <p className="text-white/80 text-sm">
            {t("tech.architectureBody")}
          </p>
        </div>
        
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 rounded-full glass-card hover:bg-white/10 transition-colors"
          aria-label={t("tech.close")}
          title={t("tech.close")}
        >
          <X className="h-4 w-4 text-white" />
        </button>
      </DialogContent>
    </Dialog>
  );
};

export default TechDialog;