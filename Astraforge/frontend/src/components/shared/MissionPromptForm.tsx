import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { FormField, Textarea, Button } from './forms';

const missionPromptSchema = z.object({
  prompt: z.string()
    .min(10, 'Mission prompt must be at least 10 characters long')
    .max(1000, 'Mission prompt must be less than 1000 characters'),
});

type MissionPromptFormData = z.infer<typeof missionPromptSchema>;

interface MissionPromptFormProps {
  onSubmit: (prompt: string) => void;
  loading?: boolean;
  className?: string;
}

const MissionPromptForm: React.FC<MissionPromptFormProps> = ({
  onSubmit,
  loading = false,
  className = '',
}) => {
  const {
    register,
    handleSubmit,
    formState: { errors, isValid },
    reset,
  } = useForm<MissionPromptFormData>({
    resolver: zodResolver(missionPromptSchema),
    mode: 'onChange',
  });

  const handleFormSubmit = (data: MissionPromptFormData) => {
    onSubmit(data.prompt);
    reset();
  };

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className={`space-y-4 ${className}`}>
      <FormField
        label="Mission Description"
        error={errors.prompt}
        required
      >
        <Textarea
          {...register('prompt')}
          placeholder="Describe your space mission idea... (e.g., 'Send a probe to Mars to study the atmosphere and search for signs of life')"
          rows={4}
          error={!!errors.prompt}
        />
      </FormField>

      <Button
        type="submit"
        loading={loading}
        disabled={!isValid || loading}
        className="w-full"
      >
        Generate Mission
      </Button>

      <p className="text-sm text-gray-400 text-center">
        Our AI will generate a detailed mission specification based on your description
      </p>
    </form>
  );
};

export default MissionPromptForm;