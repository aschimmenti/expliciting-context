<!-- SchemaValidatorComponent.vue -->
<template>
  <div class="relative min-h-screen flex flex-col">
    <!-- Original Text Panel - Fixed at top -->
    <div class="w-full bg-gray-50 p-4 border-b">
      <div v-if="currentEvent" class="prose max-w-none">
        <h3 class="font-bold mb-2">Original Text</h3>
        <p class="text-sm">{{ currentEvent.text }}</p>
        <p class="text-sm mt-2 text-gray-600">Paragraph Index: {{ currentEvent.paragraphindex }}</p>
      </div>
    </div>

    <!-- Main Content Area -->
    <div class="flex-1 flex">
      <!-- Left Panel - Validation Controls -->
      <div class="w-1/2 p-4 overflow-auto">
        <!-- File Uploads -->
        <div class="space-y-4 mb-6">
          <div>
            <label class="block text-sm font-medium mb-1">Schema File:</label>
            <input
              type="file"
              accept=".json"
              @change="handleSchemaUpload"
              class="w-full"
            >
          </div>
          
          <div>
            <label class="block text-sm font-medium mb-1">Data File:</label>
            <input
              type="file"
              accept=".json"
              @change="handleDataUpload"
              :disabled="!schema"
              class="w-full"
            >
            <p v-if="!schema" class="text-sm text-gray-500 mt-1">Please upload schema file first</p>
          </div>
        </div>

        <div v-if="jsonData">
          <!-- Event Navigation -->
          <div class="flex justify-between items-center mb-4">
            <button 
              @click="currentPage--" 
              :disabled="currentPage === 0"
              class="px-4 py-2 bg-blue-500 text-white rounded disabled:opacity-50"
            >Previous</button>
            <span>Event {{ currentPage + 1 }} of {{ totalEvents }}</span>
            <button 
              @click="currentPage++" 
              :disabled="currentPage >= totalEvents - 1"
              class="px-4 py-2 bg-blue-500 text-white rounded disabled:opacity-50"
            >Next</button>
          </div>

          <!-- Validation Section -->
          <div v-if="currentEvent" class="bg-white p-6 rounded-lg shadow-lg">
            <div class="flex justify-between items-center mb-4">
              <h2 class="text-xl font-bold">Type: {{ currentEvent.type }}</h2>
            </div>

            <!-- Schema Validation -->
            <div class="mb-6 p-4 bg-gray-50 rounded">
              <h3 class="font-semibold mb-2">Schema Validation</h3>
              
              <!-- Overall Validation -->
              <div class="mb-4 flex gap-8">
                <label class="flex items-center gap-2">
                  <input 
                    type="checkbox" 
                    :checked="getEventValidation().isOutputValid"
                    @change="toggleOutputValid"
                    class="w-4 h-4"
                  >
                  <span class="text-sm font-medium">Output is Valid</span>
                </label>
                
                <label class="flex items-center gap-2">
                  <input 
                    type="checkbox" 
                    :checked="getEventValidation().isClassificationTrue"
                    @change="toggleClassificationTrue"
                    class="w-4 h-4"
                  >
                  <span class="text-sm font-medium">Classification is True</span>
                </label>
              </div>

              <!-- Field Validation -->
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <h4 class="text-sm font-medium mb-2">Required Fields</h4>
                  <ul class="text-sm space-y-1">
                    <li v-for="field in getRequiredFields()" :key="field" 
                        class="flex items-center">
                      <span :class="{'text-green-600': isFieldPresent(field), 'text-red-600': !isFieldPresent(field)}">
                        {{ field }}
                      </span>
                    </li>
                  </ul>
                </div>
                
                <div>
                  <h4 class="text-sm font-medium mb-2">Field Validation</h4>
                  <ul class="text-sm space-y-1">
                    <li v-for="(validation, field) in getFieldValidations()" :key="field"
                        class="flex items-center justify-between">
                      <span>{{ field }}</span>
                      <div class="flex gap-2">
                        <button 
                          @click="markAsValid(field)"
                          :class="{'bg-green-500': validation.tp, 'bg-gray-200': !validation.tp}"
                          class="px-2 py-1 rounded text-xs text-white">
                          TP
                        </button>
                        <button 
                          @click="markAsFalsePositive(field)"
                          :class="{'bg-yellow-500': validation.fp, 'bg-gray-200': !validation.fp}"
                          class="px-2 py-1 rounded text-xs text-white">
                          FP
                        </button>
                        <button 
                          @click="markAsMissing(field)"
                          :class="{'bg-red-500': validation.fn, 'bg-gray-200': !validation.fn}"
                          class="px-2 py-1 rounded text-xs text-white">
                          FN
                        </button>
                        <button 
                          @click="markAsTrueNegative(field)"
                          :class="{'bg-blue-500': validation.tn, 'bg-gray-200': !validation.tn}"
                          class="px-2 py-1 rounded text-xs text-white">
                          TN
                        </button>
                      </div>
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Right Panel - JSON Display -->
      <div class="w-1/2 bg-gray-50 p-4 overflow-auto border-l">
        <div v-if="currentEvent">
          <h3 class="font-bold mb-2">Event Data</h3>
          <pre class="text-sm bg-white p-4 rounded overflow-auto">{{ JSON.stringify(currentEvent.data, null, 2) }}</pre>
          
          <div class="mt-6">
            <h3 class="font-bold mb-2">Schema Requirements</h3>
            <pre class="text-xs bg-white p-2 rounded">{{ currentSchemaInstructions }}</pre>
          </div>
        </div>
      </div>
    </div>

    <!-- Download Button -->
    <div class="fixed bottom-4 left-4">
      <button
        @click="downloadReport"
        class="px-6 py-3 bg-green-600 text-white rounded-lg shadow-lg hover:bg-green-700 flex items-center gap-2"
      >
        <span>↓</span>
        Download Report
      </button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SchemaValidatorComponent',
  
  data() {
    return {
      jsonData: null,
      schema: null,
      currentPage: 0,
      evaluations: {},
      error: null
    }
  },

  computed: {
    allEvents() {
      return this.jsonData ? this.jsonData.flatMap(item => item.events) : [];
    },
    
    totalEvents() {
      return this.allEvents.length;
    },
    
    currentEvent() {
      return this.allEvents[this.currentPage] || null;
    },

    currentSchemaInstructions() {
      if (!this.currentEvent || !this.schema) return '';
      return this.schema[this.currentEvent.type]?.instructions || '';
    }
  },

  methods: {
    handleSchemaUpload(event) {
      const file = event.target.files[0];
      if (!file) return;

      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          this.schema = JSON.parse(e.target.result);
        } catch (err) {
          this.error = 'Invalid schema JSON file';
          console.error('Error parsing schema:', err);
        }
      };
      reader.readAsText(file);
    },

    handleDataUpload(event) {
      const file = event.target.files[0];
      if (!file) return;

      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const parsed = JSON.parse(e.target.result);
          this.jsonData = parsed;
          this.initializeEvaluations();
        } catch (err) {
          this.error = 'Invalid data JSON file';
          console.error('Error parsing JSON:', err);
        }
      };
      reader.readAsText(file);
    },

    traverseTree(obj, path = '', skipArrays = false) {
      const fields = [];
      
      for (const key in obj) {
        const value = obj[key];
        const currentPath = path ? `${path}.${key}` : key;
        
        if (Array.isArray(value) && !skipArrays) {
          // Handle arrays
          value.forEach((item, index) => {
            if (item !== null && typeof item === 'object') {
              fields.push(...this.traverseTree(item, `${currentPath}[${index}]`));
            } else if (item !== undefined) {
              fields.push(`${currentPath}[${index}]`);
            }
          });
        } else if (value !== null && typeof value === 'object') {
          // Handle nested objects
          fields.push(...this.traverseTree(value, currentPath));
        } else if (value !== undefined) {
          // Handle leaf nodes (primitive values)
          fields.push(currentPath);
        }
      }
      
      return fields;
    },

    getRequiredFields() {
      if (!this.currentEvent || !this.schema) return [];
      return this.traverseTree(this.currentEvent.data);
    },

    getRequiredFieldsForEvent(event) {
      if (!event || !event.data) return [];
      return this.traverseTree(event.data);
    },

    isFieldPresent(field) {
      if (!this.currentEvent) return false;
      
      const getValueByPath = (obj, path) => {
        const parts = path.split(/[\[\].]+/).filter(Boolean);
        let current = obj;
        
        for (const part of parts) {
          if (!current) return undefined;
          
          if (part.match(/^\d+$/)) {
            const index = parseInt(part);
            if (!Array.isArray(current) || index >= current.length) {
              return undefined;
            }
            current = current[index];
          } else {
            if (!(part in current)) {
              return undefined;
            }
            current = current[part];
          }
        }
        
        return current;
      };

      const value = getValueByPath(this.currentEvent.data, field);
      return value !== undefined && value !== null && value !== '';
    },

    getFieldValidations() {
      const currentKey = `${this.currentPage}_${this.currentEvent?.type}`;
      return this.evaluations[currentKey]?.fields || {};
    },

    markFieldValidation(field, type) {
      const key = `${this.currentPage}_${this.currentEvent?.type}`;
      if (!this.evaluations[key]) {
        this.evaluations[key] = { 
          isOutputValid: false, 
          isClassificationTrue: false, 
          fields: {} 
        };
      }
      
      if (!this.evaluations[key].fields[field]) {
        this.evaluations[key].fields[field] = { 
          tp: false, 
          fp: false, 
          fn: false, 
          tn: false 
        };
      }
      
      const validation = this.evaluations[key].fields[field];
      // Reset all values
      validation.tp = false;
      validation.fp = false;
      validation.fn = false;
      validation.tn = false;
      // Set the requested type
      validation[type] = true;
    },

    markAsValid(field) {
      this.markFieldValidation(field, 'tp');
    },

    markAsFalsePositive(field) {
      this.markFieldValidation(field, 'fp');
    },

    markAsMissing(field) {
      this.markFieldValidation(field, 'fn');
    },

    markAsTrueNegative(field) {
      this.markFieldValidation(field, 'tn');
    },

    initializeEvaluations() {
      const evaluations = {};
      
      this.allEvents.forEach((event, index) => {
        const key = `${index}_${event.type}`;
        evaluations[key] = {
          isOutputValid: false,
          isClassificationTrue: false,
          fields: {}
        };
        
        const fields = this.traverseTree(event.data);
        fields.forEach(field => {
          evaluations[key].fields[field] = { 
            tp: false, 
            fp: false, 
            fn: false, 
            tn: false 
          };
        });
      });

      this.evaluations = evaluations;
    },

    getEventValidation() {
      const key = `${this.currentPage}_${this.currentEvent?.type}`;
      if (!this.evaluations[key]) {
        this.evaluations[key] = {
          isOutputValid: false,
          isClassificationTrue: false,
          fields: {}
        };
      }
      return this.evaluations[key];
    },

    toggleOutputValid() {
      const validation = this.getEventValidation();
      validation.isOutputValid = !validation.isOutputValid;
    },

    toggleClassificationTrue() {
      const validation = this.getEventValidation();
      validation.isClassificationTrue = !validation.isClassificationTrue;
    },

    calculateMetrics() {
      let totalTP = 0;
      let totalFP = 0;
      let totalFN = 0;
      let totalTN = 0;
      let validOutputs = 0;
      let trueClassifications = 0;
      let totalEvents = 0;
      let totalFields = 0;

      Object.entries(this.evaluations).forEach(([key, eventEval]) => {
        totalEvents++;
        if (eventEval.isOutputValid) validOutputs++;
        if (eventEval.isClassificationTrue) trueClassifications++;
        
        const [index, type] = key.split('_');
        const event = this.jsonData.flatMap(item => item.events)[parseInt(index)];
        const eventFields = this.traverseTree(event.data);
        totalFields += eventFields.length;
        
        eventFields.forEach(field => {
          const fieldEval = eventEval.fields[field];
          if (!fieldEval) return;
          
          if (fieldEval.tp) totalTP++;
          if (fieldEval.fp) totalFP++;
          if (fieldEval.fn) totalFN++;
          if (fieldEval.tn) totalTN++;
        });
      });

      const precision = totalTP / (totalTP + totalFP) || 0;
      const recall = totalTP / (totalTP + totalFN) || 0;
      const f1 = 2 * (precision * recall) / (precision + recall) || 0;
      const accuracy = (totalTP + totalTN) / (totalTP + totalTN + totalFP + totalFN) || 0;

      return {
        precision: precision.toFixed(2),
        recall: recall.toFixed(2),
        f1: f1.toFixed(2),
        accuracy: accuracy.toFixed(2),
        truePositives: totalTP,
        trueNegatives: totalTN,
        falsePositives: totalFP,
        falseNegatives: totalFN,
        totalFields,
        validOutputs,
        totalEvents,
        validOutputPercentage: ((validOutputs / totalEvents) * 100).toFixed(2),
        trueClassifications,
        trueClassificationPercentage: ((trueClassifications / totalEvents) * 100).toFixed(2)
      };
    },

    downloadReport() {
      const metrics = this.calculateMetrics();
      const report = {
        metrics,
        evaluations: this.evaluations
      };
      const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'evaluation_report.json';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    }
  }
}
</script>