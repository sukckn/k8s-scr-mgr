{{/*
Return the base chart name (trims if needed)
*/}}
{{- define "k8sscrmgr.name" -}}
{{- default .Chart.Name .Values.fuffixName | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Return a fully qualified name: <release>-<name>
Respects installName to force a specific root name.
*/}}
{{- define "k8sscrmgr.installName" -}}
{{- if .Values.installName -}}
{{- .Values.installName | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name (include "k8sscrmgr.name" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{/*
Common labels to apply to all resources.
*/}}
{{- define "k8sscrmgr.labels" -}}
app.kubernetes.io/name: {{ include "k8sscrmgr.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/version: {{ .Chart.AppVersion | default .Chart.Version }}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version | quote }}
{{- end -}}

{{/*
Uninstall command.
*/}}
{{- define "k8sscrmgr.uninstall" -}}
{{- printf "helm uninstall %s -n %s" .Release.Name .Release.Namespace -}}
{{- end -}}

``
