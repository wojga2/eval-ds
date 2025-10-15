import { ProjectInfo } from '@/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

interface ProjectSelectorProps {
  projects: ProjectInfo[];
  selectedProject: string | null;
  onSelectProject: (projectName: string) => void;
}

export function ProjectSelector({ projects, selectedProject, onSelectProject }: ProjectSelectorProps) {
  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">Select a Project</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {projects.map((project) => (
          <Card
            key={project.name}
            className={`cursor-pointer transition-all hover:shadow-lg ${
              selectedProject === project.name ? 'ring-2 ring-primary' : ''
            }`}
            onClick={() => onSelectProject(project.name)}
          >
            <CardHeader>
              <CardTitle className="text-lg">{project.name}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Total Samples:</span>
                <span className="font-semibold">{project.num_samples}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Success:</span>
                <Badge variant="success">{project.num_success}</Badge>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Failed:</span>
                <Badge variant="destructive">{project.num_failed}</Badge>
              </div>
              <div className="mt-4">
                <span className="text-xs text-muted-foreground">
                  {project.axial_codes.length} unique codes
                </span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

