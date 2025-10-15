import { TaskSample } from '@/types';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';

interface TaskListProps {
  tasks: TaskSample[];
  selectedTaskId: string | null;
  onSelectTask: (taskId: string) => void;
}

export function TaskList({ tasks, selectedTaskId, onSelectTask }: TaskListProps) {
  return (
    <div className="space-y-2 p-4 overflow-y-auto">
      {tasks.map((task) => (
        <Card
          key={task.sample_id}
          className={`p-4 cursor-pointer transition-all hover:shadow-md ${
            selectedTaskId === task.sample_id ? 'ring-2 ring-primary' : ''
          }`}
          onClick={() => onSelectTask(task.sample_id)}
        >
          <div className="space-y-2">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="text-xs text-muted-foreground mb-1">
                  {task.sample_id.substring(0, 8)}...
                </div>
                <div className="text-sm font-medium line-clamp-2">
                  {task.open_coding.descriptive_summary}
                </div>
              </div>
              <Badge variant={task.eval_metrics.success ? 'success' : 'destructive'}>
                {task.eval_metrics.success ? 'Pass' : 'Fail'}
              </Badge>
            </div>
            
            <div className="flex flex-wrap gap-1">
              <Badge variant="outline" className="text-xs">
                {task.axial_coding.primary_code}
              </Badge>
              {task.axial_coding.severity && (
                <Badge
                  variant={task.axial_coding.severity === 'critical' ? 'destructive' : 'secondary'}
                  className="text-xs"
                >
                  {task.axial_coding.severity}
                </Badge>
              )}
            </div>
            
            <div className="text-xs text-muted-foreground">
              Reward: {task.eval_metrics.reward.toFixed(2)}
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
}

