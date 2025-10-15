import { TaskSample, TurnContent } from '@/types';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface TaskDetailProps {
  task: TaskSample;
}

export function TaskDetail({ task }: TaskDetailProps) {
  const hasTurnSpecific = task.open_coding.failure_point_turn !== null && task.open_coding.failure_point_turn !== undefined;

  const renderTurnContent = (turn: TurnContent, index: number) => {
    const isFailurePoint = hasTurnSpecific && index === task.open_coding.failure_point_turn;
    
    return (
      <div
        key={index}
        className={`border-l-4 pl-4 py-3 ${
          turn.speaker === 'user' ? 'border-blue-300 bg-blue-50/50' : 'border-green-300 bg-green-50/50'
        } ${isFailurePoint ? 'ring-2 ring-red-500' : ''}`}
      >
        <div className="flex items-start justify-between mb-2">
          <Badge variant={turn.speaker === 'user' ? 'outline' : 'secondary'}>
            {turn.speaker}
          </Badge>
          {isFailurePoint && (
            <Badge variant="destructive" className="text-xs">
              Failure Point
            </Badge>
          )}
        </div>

        {turn.thinking && (
          <div className="mb-2 p-2 bg-yellow-50 border border-yellow-200 rounded text-xs">
            <div className="font-semibold text-yellow-800 mb-1">Thinking:</div>
            <div className="text-gray-700 whitespace-pre-wrap">{turn.thinking}</div>
          </div>
        )}

        {turn.content && (
          <div className="mb-2 text-sm whitespace-pre-wrap">{turn.content}</div>
        )}

        {turn.tool_call && (
          <div className="mb-2 p-2 bg-purple-50 border border-purple-200 rounded">
            <div className="font-semibold text-purple-800 text-xs mb-1">Tool Call:</div>
            <pre className="text-xs overflow-x-auto">
              {JSON.stringify(turn.tool_call, null, 2)}
            </pre>
          </div>
        )}

        {turn.tool_result && (
          <div className="p-2 bg-gray-50 border border-gray-200 rounded">
            <div className="font-semibold text-gray-800 text-xs mb-1">Tool Result:</div>
            <pre className="text-xs overflow-x-auto">
              {JSON.stringify(turn.tool_result, null, 2)}
            </pre>
          </div>
        )}

        {isFailurePoint && (
          <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded">
            <div className="font-semibold text-red-800 text-sm mb-1">Turn-Specific Analysis:</div>
            <div className="text-sm text-gray-700">
              <div className="mb-2">
                <span className="font-semibold">Issues:</span>
                <ul className="list-disc list-inside mt-1">
                  {task.open_coding.issues_identified.map((issue, i) => (
                    <li key={i}>{issue}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="h-full overflow-y-auto p-6 space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold mb-2">Task Detail</h2>
        <div className="text-sm text-muted-foreground">{task.sample_id}</div>
      </div>

      {/* Eval Metrics */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Evaluation Metrics</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium">Status:</span>
            <Badge variant={task.eval_metrics.success ? 'success' : 'destructive'}>
              {task.eval_metrics.success ? 'PASS' : 'FAIL'}
            </Badge>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium">Reward:</span>
            <span className="font-mono">
              {task.eval_metrics.reward != null ? task.eval_metrics.reward.toFixed(4) : 'N/A'}
            </span>
          </div>
          {task.eval_metrics.total_reward != null && (
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">Total Reward:</span>
              <span className="font-mono">{task.eval_metrics.total_reward.toFixed(4)}</span>
            </div>
          )}
          {task.eval_metrics.checks && (
            <div className="pt-2 border-t">
              <div className="text-sm font-medium mb-2">Checks:</div>
              <pre className="text-xs bg-muted p-2 rounded overflow-x-auto">
                {JSON.stringify(task.eval_metrics.checks, null, 2)}
              </pre>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Conversation */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Conversation</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {task.conversation.map((turn, index) => renderTurnContent(turn, index))}
          </div>
        </CardContent>
      </Card>

      {/* Analysis Section - Only if NOT turn-specific */}
      {!hasTurnSpecific && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Conversation-Level Analysis</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <h3 className="font-semibold text-sm mb-2">Summary</h3>
              <p className="text-sm">{task.open_coding.descriptive_summary}</p>
            </div>

            <div>
              <h3 className="font-semibold text-sm mb-2">Detailed Analysis</h3>
              <p className="text-sm whitespace-pre-wrap">{task.open_coding.detailed_analysis}</p>
            </div>

            <div>
              <h3 className="font-semibold text-sm mb-2">Issues Identified</h3>
              <ul className="list-disc list-inside text-sm space-y-1">
                {task.open_coding.issues_identified.map((issue, i) => (
                  <li key={i}>{issue}</li>
                ))}
              </ul>
            </div>

            <div>
              <h3 className="font-semibold text-sm mb-2">Observations</h3>
              <p className="text-sm whitespace-pre-wrap">{task.open_coding.observations}</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Axial Coding */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Axial Coding</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div>
            <span className="text-sm font-medium">Primary Code:</span>
            <div className="mt-1">
              <Badge variant="outline">{task.axial_coding.primary_code}</Badge>
            </div>
          </div>
          
          {task.axial_coding.secondary_codes.length > 0 && (
            <div>
              <span className="text-sm font-medium">Secondary Codes:</span>
              <div className="flex flex-wrap gap-2 mt-1">
                {task.axial_coding.secondary_codes.map((code, i) => (
                  <Badge key={i} variant="secondary">{code}</Badge>
                ))}
              </div>
            </div>
          )}

          {task.axial_coding.severity && (
            <div>
              <span className="text-sm font-medium">Severity:</span>
              <div className="mt-1">
                <Badge variant={task.axial_coding.severity === 'critical' ? 'destructive' : 'secondary'}>
                  {task.axial_coding.severity}
                </Badge>
              </div>
            </div>
          )}

          <div>
            <span className="text-sm font-medium">Rationale:</span>
            <p className="text-sm mt-1">{task.axial_coding.rationale}</p>
          </div>
        </CardContent>
      </Card>

      {/* Recommendations */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Recommendations</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm whitespace-pre-wrap">{task.open_coding.recommendations}</p>
        </CardContent>
      </Card>
    </div>
  );
}

