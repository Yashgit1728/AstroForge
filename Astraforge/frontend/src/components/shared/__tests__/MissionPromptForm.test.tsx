import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import MissionPromptForm from '../MissionPromptForm';

describe('MissionPromptForm', () => {
  it('renders form elements correctly', () => {
    const mockOnSubmit = vi.fn();
    
    render(<MissionPromptForm onSubmit={mockOnSubmit} />);

    expect(screen.getByLabelText(/mission description/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /generate mission/i })).toBeInTheDocument();
    expect(screen.getByText(/our ai will generate/i)).toBeInTheDocument();
  });

  it('validates minimum length', async () => {
    const user = userEvent.setup();
    const mockOnSubmit = vi.fn();
    
    render(<MissionPromptForm onSubmit={mockOnSubmit} />);

    const textarea = screen.getByLabelText(/mission description/i);
    const submitButton = screen.getByRole('button', { name: /generate mission/i });

    await user.type(textarea, 'short');
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/must be at least 10 characters/i)).toBeInTheDocument();
    });

    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  it('validates maximum length', async () => {
    const user = userEvent.setup();
    const mockOnSubmit = vi.fn();
    
    render(<MissionPromptForm onSubmit={mockOnSubmit} />);

    const textarea = screen.getByLabelText(/mission description/i);
    const longText = 'a'.repeat(1001);

    await user.type(textarea, longText);

    await waitFor(() => {
      expect(screen.getByText(/must be less than 1000 characters/i)).toBeInTheDocument();
    });
  });

  it('submits valid form data', async () => {
    const user = userEvent.setup();
    const mockOnSubmit = vi.fn();
    
    render(<MissionPromptForm onSubmit={mockOnSubmit} />);

    const textarea = screen.getByLabelText(/mission description/i);
    const submitButton = screen.getByRole('button', { name: /generate mission/i });
    const validPrompt = 'Send a probe to Mars to study the atmosphere';

    await user.type(textarea, validPrompt);
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith(validPrompt);
    });
  });

  it('shows loading state', () => {
    const mockOnSubmit = vi.fn();
    
    render(<MissionPromptForm onSubmit={mockOnSubmit} loading={true} />);

    const submitButton = screen.getByRole('button', { name: /generate mission/i });
    expect(submitButton).toBeDisabled();
  });

  it('disables submit button when form is invalid', async () => {
    const user = userEvent.setup();
    const mockOnSubmit = vi.fn();
    
    render(<MissionPromptForm onSubmit={mockOnSubmit} />);

    const submitButton = screen.getByRole('button', { name: /generate mission/i });
    
    // Initially disabled (empty form)
    expect(submitButton).toBeDisabled();

    // Still disabled with invalid input
    const textarea = screen.getByLabelText(/mission description/i);
    await user.type(textarea, 'short');
    
    await waitFor(() => {
      expect(submitButton).toBeDisabled();
    });
  });
});