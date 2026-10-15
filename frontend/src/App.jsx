import {
  useEffect,
  useState,
} from 'react'

import './App.css'


const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL
  || 'http://127.0.0.1:8000'


function formatLabel(value) {
  return value
    .replaceAll('_', ' ')
    .replace(/\b\w/g, (letter) =>
      letter.toUpperCase()
    )
}


function displayValue(value) {
  if (value === null || value === undefined) {
    return '—'
  }

  if (typeof value === 'boolean') {
    return value ? 'Yes' : 'No'
  }

  return String(value)
}


function App() {
  const [
    orderNumber,
    setOrderNumber,
  ] = useState('')

  const [
    question,
    setQuestion,
  ] = useState('')

  const [
    backendStatus,
    setBackendStatus,
  ] = useState('checking')

  const [
    loading,
    setLoading,
  ] = useState(false)

  const [
    result,
    setResult,
  ] = useState(null)

  const [
    error,
    setError,
  ] = useState('')

  const [
    requestId,
    setRequestId,
  ] = useState('')

  const [
    reviewDraft,
    setReviewDraft,
  ] = useState('')

  const [
    reviewLoading,
    setReviewLoading,
  ] = useState(false)

  const [
    reviewError,
    setReviewError,
  ] = useState('')

  const [
    reviewRequestId,
    setReviewRequestId,
  ] = useState('')


  useEffect(() => {
    const controller =
      new AbortController()


    async function checkBackend() {
      try {
        const response = await fetch(
          `${API_BASE_URL}/health`,
          {
            signal:
              controller.signal,
          }
        )

        if (!response.ok) {
          throw new Error(
            'Backend health check failed'
          )
        }

        setBackendStatus(
          'online'
        )
      }

      catch (healthError) {
        if (
          healthError.name
          !== 'AbortError'
        ) {
          setBackendStatus(
            'offline'
          )
        }
      }
    }


    checkBackend()


    return () => {
      controller.abort()
    }
  }, [])


  async function handleSubmit(event) {
    event.preventDefault()

    setLoading(true)

    setError('')
    setResult(null)
    setRequestId('')

    setReviewDraft('')
    setReviewError('')
    setReviewRequestId('')


    try {
      const response = await fetch(
        `${API_BASE_URL}/assistant/support`,
        {
          method:
            'POST',

          headers: {
            'Content-Type':
              'application/json',
          },

          body: JSON.stringify({
            order_number:
              orderNumber.trim(),

            question:
              question.trim(),
          }),
        }
      )


      const responseRequestId =
        response.headers.get(
          'X-Request-ID'
        )

      if (responseRequestId) {
        setRequestId(
          responseRequestId
        )
      }


      let responseBody = null

      try {
        responseBody =
          await response.json()
      }

      catch {
        responseBody = null
      }


      if (!response.ok) {
        const detail =
          responseBody?.detail
          || 'The support request failed.'

        throw new Error(
          detail
        )
      }


      setResult(
        responseBody
      )


      if (
        responseBody?.status
        === 'pending_review'
      ) {
        setReviewDraft(
          responseBody.draft_answer
          || ''
        )
      }
    }

    catch (requestError) {
      setError(
        requestError.message
        || 'Could not reach the backend.'
      )
    }

    finally {
      setLoading(false)
    }
  }


  async function handleReview(
    approved,
    useEditedAnswer,
  ) {
    if (!result?.thread_id) {
      setReviewError(
        'The workflow thread ID is missing.'
      )

      return
    }


    setReviewLoading(true)
    setReviewError('')
    setReviewRequestId('')


    try {
      const response = await fetch(
        `${API_BASE_URL}/assistant/support/review`,
        {
          method:
            'POST',

          headers: {
            'Content-Type':
              'application/json',
          },

          body: JSON.stringify({
            thread_id:
              result.thread_id,

            approved:
              approved,

            edited_answer:
              useEditedAnswer
                ? reviewDraft.trim()
                : null,
          }),
        }
      )


      const responseRequestId =
        response.headers.get(
          'X-Request-ID'
        )

      if (responseRequestId) {
        setReviewRequestId(
          responseRequestId
        )
      }


      let responseBody = null

      try {
        responseBody =
          await response.json()
      }

      catch {
        responseBody = null
      }


      if (!response.ok) {
        const detail =
          responseBody?.detail
          || 'The review request failed.'

        throw new Error(
          detail
        )
      }


      setResult(
        responseBody
      )


      if (
        responseBody?.status
        !== 'pending_review'
      ) {
        setReviewDraft('')
      }
    }

    catch (requestError) {
      setReviewError(
        requestError.message
        || 'Could not submit the review.'
      )
    }

    finally {
      setReviewLoading(false)
    }
  }


  const backendLabel = {
    checking:
      'Checking backend',

    online:
      'Backend online',

    offline:
      'Backend offline',
  }[backendStatus]


  const statusColour = {
    checking:
      '#f5c451',

    online:
      '#45d483',

    offline:
      '#ff6b6b',
  }[backendStatus]


  const responseText =
    result?.answer
    || result?.draft_answer


  return (
    <main className="app-shell">

      <header className="topbar">

        <div>

          <p className="eyebrow">
            D2C RETURNS COPILOT
          </p>

          <h1>
            Customer Support Console
          </h1>

          <p className="subtitle">
            AI-assisted support for returns,
            order questions, and shipment tracking.
          </p>

        </div>


        <div className="backend-status">

          <span
            className="status-dot"
            style={{
              background:
                statusColour,
            }}
          >
          </span>

          {backendLabel}

        </div>

      </header>


      <section className="workspace">

        <section className="request-panel">

          <div className="panel-heading">

            <p className="panel-label">
              NEW REQUEST
            </p>

            <h2>
              Ask the support assistant
            </h2>

            <p>
              Enter an order number and the
              customer's question.
            </p>

          </div>


          <form
            className="support-form"
            onSubmit={handleSubmit}
          >

            <div className="form-group">

              <label htmlFor="order-number">
                Order number
              </label>

              <input
                id="order-number"
                type="text"
                placeholder="e.g. ORD-1001"
                value={orderNumber}
                disabled={
                  loading
                  || reviewLoading
                }
                onChange={(event) =>
                  setOrderNumber(
                    event.target.value
                  )
                }
              />

            </div>


            <div className="form-group">

              <label htmlFor="question">
                Customer question
              </label>

              <textarea
                id="question"
                rows="7"
                placeholder="e.g. Can I return this item?"
                value={question}
                disabled={
                  loading
                  || reviewLoading
                }
                onChange={(event) =>
                  setQuestion(
                    event.target.value
                  )
                }
              />

            </div>


            <button
              className="submit-button"
              type="submit"
              disabled={
                loading
                || reviewLoading
                || !orderNumber.trim()
                || !question.trim()
              }
            >

              {
                loading
                  ? 'Running assistant...'
                  : 'Run support assistant'
              }

            </button>

          </form>

        </section>


        <section className="response-panel">

          <div className="panel-heading">

            <p className="panel-label">
              ASSISTANT RESPONSE
            </p>

            <h2>
              Result
            </h2>

          </div>


          {
            !loading
            && !result
            && !error
            && (

              <div className="empty-state">

                <div className="empty-icon">
                  AI
                </div>

                <h3>
                  No request yet
                </h3>

                <p>
                  Submit a customer question
                  to see the assistant response,
                  routing decision, sources,
                  and workflow status.
                </p>

              </div>

            )
          }


          {
            loading
            && (

              <div className="empty-state">

                <div className="empty-icon">
                  AI
                </div>

                <h3>
                  Running workflow
                </h3>

                <p>
                  The request is being routed
                  through the support assistant.
                  Local model generation may
                  take a few seconds.
                </p>

              </div>

            )
          }


          {
            error
            && !loading
            && (

              <div className="local-preview">

                <p className="preview-label">
                  REQUEST FAILED
                </p>


                <div className="error-note">

                  <strong>
                    Could not complete request
                  </strong>

                  <p>
                    {error}
                  </p>

                </div>


                {
                  requestId
                  && (

                    <div className="preview-row">

                      <span>
                        Request ID
                      </span>

                      <strong>
                        {requestId}
                      </strong>

                    </div>

                  )
                }

              </div>

            )
          }


          {
            result
            && !loading
            && (

              <div className="local-preview">

                <p className="preview-label">
                  WORKFLOW RESULT
                </p>


                <div className="preview-row">

                  <span>
                    Intent
                  </span>

                  <strong>
                    {result.intent}
                  </strong>

                </div>


                <div className="preview-row">

                  <span>
                    Status
                  </span>

                  <strong>
                    {result.status}
                  </strong>

                </div>


                {
                  result.thread_id
                  && (

                    <div className="preview-row">

                      <span>
                        Thread ID
                      </span>

                      <strong>
                        {result.thread_id}
                      </strong>

                    </div>

                  )
                }


                {
                  requestId
                  && (

                    <div className="preview-row">

                      <span>
                        Initial Request ID
                      </span>

                      <strong>
                        {requestId}
                      </strong>

                    </div>

                  )
                }


                {
                  reviewRequestId
                  && (

                    <div className="preview-row">

                      <span>
                        Review Request ID
                      </span>

                      <strong>
                        {reviewRequestId}
                      </strong>

                    </div>

                  )
                }


                {
                  responseText
                  && (

                    <div className="preview-question">

                      <span>
                        {
                          result.status
                          === 'pending_review'
                            ? 'Draft answer'
                            : 'Assistant answer'
                        }
                      </span>

                      <p>
                        {responseText}
                      </p>

                    </div>

                  )
                }


                {
                  result.status
                  === 'pending_review'
                  && (

                    <>

                      <div className="review-alert">

                        <strong>
                          Human review required
                        </strong>

                        <p>
                          LangGraph paused this
                          workflow before the
                          response is sent to the
                          customer.
                        </p>

                      </div>


                      <div className="review-panel">

                        <div className="review-heading">

                          <p className="preview-label">
                            HUMAN REVIEW
                          </p>

                          <h3>
                            Review the draft
                          </h3>

                          <p>
                            Approve the original
                            response, edit it before
                            approval, or reject it.
                          </p>

                        </div>


                        <label
                          className="review-label"
                          htmlFor="review-draft"
                        >
                          Editable draft
                        </label>


                        <textarea
                          id="review-draft"
                          className="review-editor"
                          value={reviewDraft}
                          disabled={reviewLoading}
                          onChange={(event) =>
                            setReviewDraft(
                              event.target.value
                            )
                          }
                        />


                        {
                          reviewError
                          && (

                            <div className="error-note">

                              <strong>
                                Review failed
                              </strong>

                              <p>
                                {reviewError}
                              </p>

                            </div>

                          )
                        }


                        {
                          reviewLoading
                          && (

                            <p className="review-progress">
                              Resuming persisted
                              workflow...
                            </p>

                          )
                        }


                        <div className="review-actions">

                          <button
                            type="button"
                            className="review-button reject"
                            disabled={reviewLoading}
                            onClick={() =>
                              handleReview(
                                false,
                                false,
                              )
                            }
                          >
                            Reject
                          </button>


                          <button
                            type="button"
                            className="review-button secondary"
                            disabled={reviewLoading}
                            onClick={() =>
                              handleReview(
                                true,
                                false,
                              )
                            }
                          >
                            Approve draft
                          </button>


                          <button
                            type="button"
                            className="review-button primary"
                            disabled={
                              reviewLoading
                              || !reviewDraft.trim()
                            }
                            onClick={() =>
                              handleReview(
                                true,
                                true,
                              )
                            }
                          >
                            Edit & Approve
                          </button>

                        </div>

                      </div>

                    </>

                  )
                }


                {
                  result.decision
                  && (

                    <>

                      <p className="preview-label">
                        RETURN DECISION
                      </p>

                      {
                        Object.entries(
                          result.decision
                        ).map(
                          ([
                            key,
                            value,
                          ]) => (

                            <div
                              className="preview-row"
                              key={key}
                            >

                              <span>
                                {
                                  formatLabel(
                                    key
                                  )
                                }
                              </span>

                              <strong>
                                {
                                  displayValue(
                                    value
                                  )
                                }
                              </strong>

                            </div>

                          )
                        )
                      }

                    </>

                  )
                }


                {
                  result.shipment
                  && (

                    <>

                      <p className="preview-label">
                        SHIPMENT
                      </p>

                      {
                        Object.entries(
                          result.shipment
                        ).map(
                          ([
                            key,
                            value,
                          ]) => (

                            <div
                              className="preview-row"
                              key={key}
                            >

                              <span>
                                {
                                  formatLabel(
                                    key
                                  )
                                }
                              </span>

                              <strong>
                                {
                                  displayValue(
                                    value
                                  )
                                }
                              </strong>

                            </div>

                          )
                        )
                      }

                    </>

                  )
                }


                {
                  result.courier_status
                  && (

                    <div className="preview-row">

                      <span>
                        Courier status
                      </span>

                      <strong>
                        {result.courier_status}
                      </strong>

                    </div>

                  )
                }


                {
                  result.validation_issues
                    ?.length > 0
                  && (

                    <>

                      <p className="preview-label">
                        VALIDATION ISSUES
                      </p>

                      {
                        result.validation_issues
                          .map(
                            (
                              issue,
                              index
                            ) => (

                              <div
                                className="preview-question"
                                key={
                                  `${issue}-${index}`
                                }
                              >

                                <span>
                                  Issue {
                                    index + 1
                                  }
                                </span>

                                <p>
                                  {issue}
                                </p>

                              </div>

                            )
                          )
                      }

                    </>

                  )
                }


                {
                  result.sources
                    ?.length > 0
                  && (

                    <>

                      <p className="preview-label">
                        POLICY SOURCES
                      </p>

                      {
                        result.sources.map(
                          (
                            source,
                            index
                          ) => (

                            <div
                              className="preview-question"
                              key={
                                `${source.source}-${source.heading}-${index}`
                              }
                            >

                              <span>
                                Source {
                                  source.number
                                  || index + 1
                                }
                              </span>

                              <p>
                                <strong>
                                  {source.heading}
                                </strong>

                                <br />

                                {source.source}

                                {
                                  source.region
                                  && (
                                    <>
                                      {' · '}
                                      {source.region}
                                    </>
                                  )
                                }

                                {
                                  typeof source.score
                                  === 'number'
                                  && (
                                    <>
                                      {' · Score '}
                                      {
                                        source.score
                                          .toFixed(4)
                                      }
                                    </>
                                  )
                                }

                              </p>

                            </div>

                          )
                        )
                      }

                    </>

                  )
                }

              </div>

            )
          }

        </section>

      </section>

    </main>
  )
}


export default App