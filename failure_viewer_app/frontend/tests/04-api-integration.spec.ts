import { test, expect } from '@playwright/test';

test.describe('API Integration', () => {
  const apiBaseUrl = 'http://100.95.221.45:9000/api';

  test('should fetch root endpoint', async ({ request }) => {
    const response = await request.get('http://100.95.221.45:9000/');
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    expect(data).toHaveProperty('message');
    expect(data.message).toContain('Failure Viewer App');
  });

  test('should fetch list of projects', async ({ request }) => {
    const response = await request.get(`${apiBaseUrl}/projects`);
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    expect(data).toHaveProperty('projects');
    expect(Array.isArray(data.projects)).toBe(true);
    
    if (data.projects.length > 0) {
      const project = data.projects[0];
      expect(project).toHaveProperty('name');
      expect(project).toHaveProperty('path');
      expect(project).toHaveProperty('num_samples');
      expect(project).toHaveProperty('num_success');
      expect(project).toHaveProperty('num_failed');
      expect(project).toHaveProperty('axial_codes');
    }
  });

  test('should fetch tasks for a project', async ({ request }) => {
    // First get list of projects
    const projectsResponse = await request.get(`${apiBaseUrl}/projects`);
    const projectsData = await projectsResponse.json();
    
    if (projectsData.projects && projectsData.projects.length > 0) {
      const projectName = projectsData.projects[0].name;
      
      // Fetch tasks for this project
      const tasksResponse = await request.get(`${apiBaseUrl}/projects/${projectName}`);
      expect(tasksResponse.status()).toBe(200);
      
      const data = await tasksResponse.json();
      expect(data).toHaveProperty('samples');
      expect(Array.isArray(data.samples)).toBe(true);
      
      if (data.samples.length > 0) {
        const task = data.samples[0];
        expect(task).toHaveProperty('sample_id');
        expect(task).toHaveProperty('conversation');
        expect(task).toHaveProperty('eval_metrics');
        expect(task).toHaveProperty('open_coding');
        expect(task).toHaveProperty('axial_coding');
      }
    }
  });

  test('should return 404 for non-existent project', async ({ request }) => {
    const response = await request.get(`${apiBaseUrl}/projects/nonexistent_project_xyz`);
    expect(response.status()).toBe(404);
  });

  test('should validate project response schema', async ({ request }) => {
    const response = await request.get(`${apiBaseUrl}/projects`);
    const data = await response.json();
    
    if (data.projects && data.projects.length > 0) {
      data.projects.forEach((project: any) => {
        expect(typeof project.name).toBe('string');
        expect(typeof project.path).toBe('string');
        expect(typeof project.num_samples).toBe('number');
        expect(typeof project.num_success).toBe('number');
        expect(typeof project.num_failed).toBe('number');
        expect(Array.isArray(project.axial_codes)).toBe(true);
      });
    }
  });

  test('should validate task response schema', async ({ request }) => {
    const projectsResponse = await request.get(`${apiBaseUrl}/projects`);
    const projectsData = await projectsResponse.json();
    
    if (projectsData.projects && projectsData.projects.length > 0) {
      const projectName = projectsData.projects[0].name;
      const tasksResponse = await request.get(`${apiBaseUrl}/projects/${projectName}`);
      const tasksData = await tasksResponse.json();
      
      if (tasksData.samples && tasksData.samples.length > 0) {
        const task = tasksData.samples[0];
        
        // Validate top-level fields
        expect(typeof task.sample_id).toBe('string');
        expect(Array.isArray(task.conversation)).toBe(true);
        expect(typeof task.eval_metrics).toBe('object');
        expect(typeof task.open_coding).toBe('object');
        expect(typeof task.axial_coding).toBe('object');
        
        // Validate eval_metrics
        expect(typeof task.eval_metrics.success).toBe('boolean');
        
        // Validate open_coding
        expect(typeof task.open_coding.descriptive_summary).toBe('string');
        expect(typeof task.open_coding.detailed_analysis).toBe('string');
        expect(Array.isArray(task.open_coding.issues_identified)).toBe(true);
        
        // Validate axial_coding
        expect(typeof task.axial_coding.primary_code).toBe('string');
        expect(Array.isArray(task.axial_coding.secondary_codes)).toBe(true);
        expect(typeof task.axial_coding.rationale).toBe('string');
      }
    }
  });

  test('should handle conversation turn structure', async ({ request }) => {
    const projectsResponse = await request.get(`${apiBaseUrl}/projects`);
    const projectsData = await projectsResponse.json();
    
    if (projectsData.projects && projectsData.projects.length > 0) {
      const projectName = projectsData.projects[0].name;
      const tasksResponse = await request.get(`${apiBaseUrl}/projects/${projectName}`);
      const tasksData = await tasksResponse.json();
      
      if (tasksData.samples && tasksData.samples.length > 0 && tasksData.samples[0].conversation.length > 0) {
        const turn = tasksData.samples[0].conversation[0];
        
        // Every turn should have a speaker
        expect(turn).toHaveProperty('speaker');
        expect(typeof turn.speaker).toBe('string');
        
        // Should have at least one of: content, tool_call, tool_result
        const hasContent = 'content' in turn;
        const hasToolCall = 'tool_call' in turn;
        const hasToolResult = 'tool_result' in turn;
        
        expect(hasContent || hasToolCall || hasToolResult).toBe(true);
      }
    }
  });

  test('should handle API connectivity', async ({ request }) => {
    // Test basic API connectivity
    const response = await request.get(`${apiBaseUrl}/projects`);
    
    // Should get a successful response
    expect(response.ok()).toBe(true);
    expect(response.status()).toBe(200);
  });

  test('should handle empty project gracefully', async ({ request }) => {
    // This test checks that even if a project has no tasks, API doesn't crash
    const projectsResponse = await request.get(`${apiBaseUrl}/projects`);
    const projectsData = await projectsResponse.json();
    
    if (projectsData.projects && projectsData.projects.length > 0) {
      const projectName = projectsData.projects[0].name;
      const tasksResponse = await request.get(`${apiBaseUrl}/projects/${projectName}`);
      
      // Should return 200 even if empty
      expect(tasksResponse.status()).toBe(200);
      
      const tasksData = await tasksResponse.json();
      expect(tasksData).toHaveProperty('samples');
      expect(Array.isArray(tasksData.samples)).toBe(true);
    }
  });
});

