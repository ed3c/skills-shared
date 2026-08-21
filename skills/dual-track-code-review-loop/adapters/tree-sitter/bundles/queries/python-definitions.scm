; Definition sites only. Every capture below is a region of bytes with a
; shape; none of them is a symbol, a binding or a call edge, and the adapter
; that runs this query is fixed at SYNTACTIC_CANDIDATE so that none of them can
; be recorded as one.
(function_definition
  name: (identifier) @definition.function.name)

(class_definition
  name: (identifier) @definition.class.name)
