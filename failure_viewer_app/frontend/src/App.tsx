import { useState, useEffect } from 'react';
import { ProjectInfo, TaskSample } from '@/types';
import { ProjectSelector } from '@/components/ProjectSelector';
import { FilterBar } from '@/components/FilterBar';
import { TaskList } from '@/components/TaskList';
import { TaskDetail } from '@/components/TaskDetail';
import { Button } from '@/components/ui/button';

function App() {
  const [projects, setProjects] = useState<ProjectInfo[]>([]);
  const [selectedProject, setSelectedProject] = useState<string | null>(null);
  const [allTasks, setAllTasks] = useState<TaskSample[]>([]);
  const [filteredTasks, setFilteredTasks] = useState<TaskSample[]>([]);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [selectedCodes, setSelectedCodes] = useState<string[]>([]);
  const [passFailFilter, setPassFailFilter] = useState<'pass' | 'fail' | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load projects on mount
  useEffect(() => {
    fetchProjects();
  }, []);

  // Load tasks when project is selected
  useEffect(() => {
    if (selectedProject) {
      fetchTasks(selectedProject);
    }
  }, [selectedProject]);

  // Apply filters when tasks or filters change
  useEffect(() => {
    applyFilters();
  }, [allTasks, selectedCodes, passFailFilter]);

  const fetchProjects = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/projects');
      if (!response.ok) throw new Error('Failed to fetch projects');
      const data = await response.json();
      setProjects(data.projects);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load projects');
    } finally {
      setLoading(false);
    }
  };

  const fetchTasks = async (projectName: string) => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`/api/projects/${projectName}`);
      if (!response.ok) throw new Error('Failed to fetch tasks');
      const data = await response.json();
      setAllTasks(data.samples);
      setSelectedTaskId(null);
      setSelectedCodes([]);
      setPassFailFilter(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load tasks');
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = () => {
    let filtered = [...allTasks];

    // Apply pass/fail filter
    if (passFailFilter === 'pass') {
      filtered = filtered.filter(t => t.eval_metrics.success);
    } else if (passFailFilter === 'fail') {
      filtered = filtered.filter(t => !t.eval_metrics.success);
    }

    // Apply code filter
    if (selectedCodes.length > 0) {
      filtered = filtered.filter(task => {
        const allCodes = [
          task.axial_coding.primary_code,
          ...task.axial_coding.secondary_codes
        ];
        return selectedCodes.some(code => allCodes.includes(code));
      });
    }

    setFilteredTasks(filtered);
  };

  const handleBackToProjects = () => {
    setSelectedProject(null);
    setAllTasks([]);
    setFilteredTasks([]);
    setSelectedTaskId(null);
    setSelectedCodes([]);
    setPassFailFilter(null);
  };

  const selectedTask = filteredTasks.find(t => t.sample_id === selectedTaskId);
  const currentProject = projects.find(p => p.name === selectedProject);

  if (loading && projects.length === 0) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-xl">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-xl text-red-600">Error: {error}</div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-background">
      {/* Header */}
      <header className="border-b p-4 bg-white">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold">Failure Viewer App</h1>
          {selectedProject && (
            <Button variant="outline" onClick={handleBackToProjects}>
              ← Back to Projects
            </Button>
          )}
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 overflow-hidden">
        {!selectedProject ? (
          /* Project Selection View */
          <div className="p-6 overflow-y-auto h-full">
            <ProjectSelector
              projects={projects}
              selectedProject={selectedProject}
              onSelectProject={setSelectedProject}
            />
          </div>
        ) : (
          /* Task Browser View */
          <div className="h-full flex flex-col">
            {/* Project Header */}
            <div className="p-4 border-b bg-muted/50">
              <h2 className="text-xl font-semibold">{selectedProject}</h2>
              {currentProject && (
                <div className="text-sm text-muted-foreground mt-1">
                  {currentProject.num_samples} total samples • {currentProject.num_success} success • {currentProject.num_failed} failed
                </div>
              )}
            </div>

            {/* Filters */}
            {currentProject && (
              <FilterBar
                availableCodes={currentProject.axial_codes}
                selectedCodes={selectedCodes}
                onCodesChange={setSelectedCodes}
                passFailFilter={passFailFilter}
                onPassFailChange={setPassFailFilter}
                totalCount={filteredTasks.length}
              />
            )}

            {/* Task List and Detail */}
            <div className="flex-1 flex overflow-hidden">
              {/* Task List */}
              <div className="w-1/3 border-r overflow-y-auto">
                {loading ? (
                  <div className="p-4 text-center">Loading tasks...</div>
                ) : (
                  <TaskList
                    tasks={filteredTasks}
                    selectedTaskId={selectedTaskId}
                    onSelectTask={setSelectedTaskId}
                  />
                )}
              </div>

              {/* Task Detail */}
              <div className="flex-1 overflow-hidden">
                {selectedTask ? (
                  <TaskDetail task={selectedTask} />
                ) : (
                  <div className="flex items-center justify-center h-full text-muted-foreground">
                    Select a task to view details
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;

