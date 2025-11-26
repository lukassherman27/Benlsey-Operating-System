'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
import { ThumbsUp, ThumbsDown, AlertTriangle } from 'lucide-react'
import { api } from '@/lib/api'
import { toast } from 'sonner'

interface FeedbackButtonsProps {
  featureType: string
  featureId: string
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  currentValue?: any
  compact?: boolean
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  onFeedbackSubmit?: (feedback: any) => void
}

export function FeedbackButtons({
  featureType,
  featureId,
  currentValue,
  compact = false,
  onFeedbackSubmit
}: FeedbackButtonsProps) {
  const [showDialog, setShowDialog] = useState(false)
  const [feedbackType, setFeedbackType] = useState<'positive' | 'negative' | 'issue' | null>(null)
  const [issueTypes, setIssueTypes] = useState({
    incorrect_data: false,
    wrong_calculation: false,
    not_working: false,
    confusing: false,
    other: false
  })
  const [feedbackText, setFeedbackText] = useState('')
  const [expectedValue, setExpectedValue] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const handleThumbsUp = async () => {
    setSubmitting(true)
    try {
      await api.logFeedback({
        feature_type: featureType,
        feature_id: featureId,
        helpful: true,
        current_value: currentValue?.toString()
      })
      toast.success('Thanks for your feedback!')
      onFeedbackSubmit?.({ helpful: true })
    } catch (error) {
      console.error('Failed to submit feedback:', error)
      toast.error('Failed to submit feedback')
    } finally {
      setSubmitting(false)
    }
  }

  const handleThumbsDown = () => {
    setFeedbackType('negative')
    setShowDialog(true)
  }

  const handleIssue = () => {
    setFeedbackType('issue')
    setShowDialog(true)
  }

  const handleSubmitFeedback = async () => {
    if (!feedbackText.trim()) {
      toast.error('Please provide details about the issue')
      return
    }

    setSubmitting(true)
    try {
      const selectedIssues = Object.entries(issueTypes)
        .filter(([_, selected]) => selected)
        .map(([type, _]) => type)

      await api.logFeedback({
        feature_type: featureType,
        feature_id: featureId,
        helpful: false,
        issue_type: selectedIssues.join(', '),
        feedback_text: feedbackText,
        expected_value: expectedValue || undefined,
        current_value: currentValue?.toString() || undefined,
        context: {
          feedback_type: feedbackType,
          timestamp: new Date().toISOString()
        }
      })

      toast.success('Feedback submitted - thank you!')
      onFeedbackSubmit?.({
        helpful: false,
        issue_type: selectedIssues,
        feedback_text: feedbackText
      })

      // Reset and close
      setShowDialog(false)
      setFeedbackText('')
      setExpectedValue('')
      setIssueTypes({
        incorrect_data: false,
        wrong_calculation: false,
        not_working: false,
        confusing: false,
        other: false
      })
    } catch (error) {
      console.error('Failed to submit feedback:', error)
      toast.error('Failed to submit feedback. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <>
      <div className={compact ? "flex gap-1" : "flex gap-2"}>
        <Button
          variant="ghost"
          size={compact ? "sm" : "default"}
          onClick={handleThumbsUp}
          disabled={submitting}
          className="hover:bg-green-50"
        >
          <ThumbsUp className={compact ? "h-3 w-3" : "h-4 w-4"} />
        </Button>
        <Button
          variant="ghost"
          size={compact ? "sm" : "default"}
          onClick={handleThumbsDown}
          disabled={submitting}
          className="hover:bg-red-50"
        >
          <ThumbsDown className={compact ? "h-3 w-3" : "h-4 w-4"} />
        </Button>
        {!compact && (
          <Button
            variant="ghost"
            size="default"
            onClick={handleIssue}
            disabled={submitting}
            className="hover:bg-yellow-50"
          >
            <AlertTriangle className="h-4 w-4 mr-2" />
            Report Issue
          </Button>
        )}
      </div>

      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>
              {feedbackType === 'issue' ? 'Report an Issue' : 'What\'s wrong?'}
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-4">
            {/* Issue Type Checkboxes */}
            <div className="space-y-2">
              <Label>What&apos;s the issue? (select all that apply)</Label>
              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="incorrect_data"
                    checked={issueTypes.incorrect_data}
                    onCheckedChange={(checked) =>
                      setIssueTypes(prev => ({ ...prev, incorrect_data: checked as boolean }))
                    }
                  />
                  <label htmlFor="incorrect_data" className="text-sm cursor-pointer">
                    Incorrect data
                  </label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="wrong_calculation"
                    checked={issueTypes.wrong_calculation}
                    onCheckedChange={(checked) =>
                      setIssueTypes(prev => ({ ...prev, wrong_calculation: checked as boolean }))
                    }
                  />
                  <label htmlFor="wrong_calculation" className="text-sm cursor-pointer">
                    Wrong calculation
                  </label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="not_working"
                    checked={issueTypes.not_working}
                    onCheckedChange={(checked) =>
                      setIssueTypes(prev => ({ ...prev, not_working: checked as boolean }))
                    }
                  />
                  <label htmlFor="not_working" className="text-sm cursor-pointer">
                    Feature not working
                  </label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="confusing"
                    checked={issueTypes.confusing}
                    onCheckedChange={(checked) =>
                      setIssueTypes(prev => ({ ...prev, confusing: checked as boolean }))
                    }
                  />
                  <label htmlFor="confusing" className="text-sm cursor-pointer">
                    Confusing/unclear
                  </label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="other"
                    checked={issueTypes.other}
                    onCheckedChange={(checked) =>
                      setIssueTypes(prev => ({ ...prev, other: checked as boolean }))
                    }
                  />
                  <label htmlFor="other" className="text-sm cursor-pointer">
                    Other
                  </label>
                </div>
              </div>
            </div>

            {/* Feedback Text - REQUIRED */}
            <div className="space-y-2">
              <Label htmlFor="feedback">
                Explain the issue <span className="text-red-500">*</span>
              </Label>
              <Textarea
                id="feedback"
                placeholder="E.g., The outstanding invoice number is different from what shows in the widget below. Should be $4.87M but showing $5.47M"
                value={feedbackText}
                onChange={(e) => setFeedbackText(e.target.value)}
                rows={4}
                className="resize-none"
                required
              />
              <p className="text-xs text-muted-foreground">
                Please provide as much detail as possible
              </p>
            </div>

            {/* Current Value Display */}
            {currentValue && (
              <div className="space-y-2">
                <Label>Current value shown:</Label>
                <div className="p-2 bg-gray-50 rounded border text-sm">
                  {currentValue.toString()}
                </div>
              </div>
            )}

            {/* Expected Value */}
            <div className="space-y-2">
              <Label htmlFor="expected">Expected value (optional)</Label>
              <Input
                id="expected"
                placeholder="What you expected to see"
                value={expectedValue}
                onChange={(e) => setExpectedValue(e.target.value)}
              />
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowDialog(false)}
              disabled={submitting}
            >
              Cancel
            </Button>
            <Button
              onClick={handleSubmitFeedback}
              disabled={submitting || !feedbackText.trim()}
            >
              {submitting ? 'Submitting...' : 'Submit Feedback'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
