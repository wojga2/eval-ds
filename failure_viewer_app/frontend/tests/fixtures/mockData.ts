import { ProjectInfo, TaskSample } from '../../src/types';

export const mockProjects: ProjectInfo[] = [
  {
    name: 'test_project_1',
    path: '/mock/path/test_project_1',
    num_samples: 10,
    num_success: 6,
    num_failed: 4,
    axial_codes: ['tool_error', 'procedure_gap', 'communication_breakdown']
  },
  {
    name: 'test_project_2',
    path: '/mock/path/test_project_2',
    num_samples: 5,
    num_success: 2,
    num_failed: 3,
    axial_codes: ['escalation_problem', 'tool_error']
  }
];

export const mockTasks: TaskSample[] = [
  {
    sample_id: 'sample-001',
    task_name: 'Test Task 1',
    conversation: [
      {
        speaker: 'user',
        content: 'Hello, I need help with my account'
      },
      {
        speaker: 'assistant',
        content: 'I can help you with that. Let me check your account.',
        thinking: 'User needs account assistance'
      },
      {
        speaker: 'assistant',
        tool_call: {
          name: 'check_account',
          arguments: { user_id: '123' }
        }
      },
      {
        speaker: 'system',
        tool_result: {
          status: 'active',
          balance: 100
        }
      },
      {
        speaker: 'assistant',
        content: 'Your account is active with a balance of $100.'
      }
    ],
    eval_metrics: {
      success: true,
      reward: 1.0,
      total_reward: 1.0,
      checks: {
        completed: true,
        accurate: true
      }
    },
    open_coding: {
      descriptive_summary: 'Successfully handled account inquiry',
      failure_point_turn: null,
      detailed_analysis: 'The agent correctly identified the user need and retrieved account information.',
      issues_identified: [],
      observations: 'Smooth interaction with proper tool usage',
      recommendations: 'Continue this approach for similar queries'
    },
    axial_coding: {
      primary_code: 'tool_error',
      secondary_codes: ['procedure_gap'],
      severity: 'minor',
      rationale: 'Minor tool usage issue but overall successful'
    }
  },
  {
    sample_id: 'sample-002',
    task_name: 'Test Task 2',
    conversation: [
      {
        speaker: 'user',
        content: 'My service is not working'
      },
      {
        speaker: 'assistant',
        content: 'Let me troubleshoot that for you.'
      }
    ],
    eval_metrics: {
      success: false,
      reward: 0.0,
      total_reward: 0.0,
      checks: {
        completed: false,
        accurate: false
      }
    },
    open_coding: {
      descriptive_summary: 'Failed to resolve service issue',
      failure_point_turn: 1,
      detailed_analysis: 'The agent did not follow proper troubleshooting steps.',
      issues_identified: [
        'Skipped diagnostics',
        'No tool usage',
        'Premature conclusion'
      ],
      observations: 'Agent rushed through troubleshooting',
      recommendations: 'Implement step-by-step diagnostic checklist'
    },
    axial_coding: {
      primary_code: 'procedure_gap',
      secondary_codes: ['communication_breakdown'],
      severity: 'critical',
      rationale: 'Failed to follow required procedures'
    }
  },
  {
    sample_id: 'sample-003',
    task_name: 'Test Task 3',
    conversation: [
      {
        speaker: 'user',
        content: 'I want to escalate this issue'
      },
      {
        speaker: 'assistant',
        content: 'Let me transfer you to a supervisor.',
        tool_call: {
          name: 'escalate',
          arguments: { reason: 'user_request' }
        }
      }
    ],
    eval_metrics: {
      success: true,
      reward: 0.8,
      total_reward: null,
      checks: null
    },
    open_coding: {
      descriptive_summary: 'Properly escalated customer request',
      failure_point_turn: null,
      detailed_analysis: 'Agent correctly identified escalation need and executed it.',
      issues_identified: [],
      observations: 'Quick and appropriate escalation',
      recommendations: 'Good pattern for escalation scenarios'
    },
    axial_coding: {
      primary_code: 'escalation_problem',
      secondary_codes: [],
      severity: 'minor',
      rationale: 'Escalation handled well'
    }
  }
];

