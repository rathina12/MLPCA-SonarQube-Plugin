package io.mlpca.sonar;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import org.sonar.api.batch.fs.InputFile;
import org.sonar.api.batch.rule.Severity;
import org.sonar.api.batch.sensor.Sensor;
import org.sonar.api.batch.sensor.SensorContext;
import org.sonar.api.batch.sensor.SensorDescriptor;
import org.sonar.api.batch.sensor.issue.NewExternalIssue;
import org.sonar.api.batch.sensor.issue.NewIssueLocation;
import org.sonar.api.rules.RuleType;
import org.sonar.api.utils.log.Logger;
import org.sonar.api.utils.log.Loggers;

public final class MlpcaSensor implements Sensor {
  public static final String REPORT_PATH_KEY = "sonar.mlpca.reportPath";
  private static final Logger LOG = Loggers.get(MlpcaSensor.class);
  private final ObjectMapper mapper = new ObjectMapper();

  @Override
  public void describe(SensorDescriptor descriptor) {
    descriptor.name("MLPCA C/C++ memory leak report importer");
  }

  @Override
  public void execute(SensorContext context) {
    String configured = context.config().get(REPORT_PATH_KEY).orElse(".mlpca/issues.json");
    Path report = context.fileSystem().baseDir().toPath().resolve(configured).normalize();
    if (!Files.isRegularFile(report)) {
      LOG.info("MLPCA report not found at {}. Run the analyzer before SonarScanner.", report);
      return;
    }
    try {
      JsonNode root = mapper.readTree(report.toFile());
      JsonNode issues = root.path("issues");
      if (!issues.isArray()) {
        LOG.warn("MLPCA report has no 'issues' array: {}", report);
        return;
      }
      int imported = 0;
      for (JsonNode item : issues) {
        if (importIssue(context, item)) imported++;
      }
      LOG.info("MLPCA imported {} external issue(s) from {}", imported, report);
    } catch (IOException | RuntimeException ex) {
      throw new IllegalStateException("Failed to import MLPCA report: " + report, ex);
    }
  }

  private boolean importIssue(SensorContext context, JsonNode item) {
    String ruleId = text(item, "ruleId", "MLPCA");
    String severityText = text(item, "severity", "MAJOR");
    JsonNode loc = item.path("primaryLocation");
    String filePath = text(loc, "filePath", "");
    String message = text(loc, "message", "MLPCA memory issue");
    int line = Math.max(1, loc.path("textRange").path("startLine").asInt(1));
    if (filePath.isBlank()) return false;

    InputFile input = context.fileSystem().inputFile(context.fileSystem().predicates().hasPath(filePath));
    if (input == null) {
      LOG.warn("MLPCA issue skipped because file is not indexed by SonarScanner: {}", filePath);
      return false;
    }
    int safeLine = Math.min(line, Math.max(1, input.lines()));
    NewExternalIssue issue = context.newExternalIssue()
        .engineId("mlpca")
        .ruleId(ruleId)
        .severity(parseSeverity(severityText))
        .type(RuleType.BUG)
        .remediationEffortMinutes(item.path("effortMinutes").asLong(10));
    NewIssueLocation location = issue.newLocation()
        .on(input)
        .at(input.selectLine(safeLine))
        .message(message);
    issue.at(location).save();
    return true;
  }

  private static String text(JsonNode node, String field, String fallback) {
    JsonNode v = node.path(field);
    return v.isTextual() ? v.asText() : fallback;
  }

  private static Severity parseSeverity(String value) {
    try { return Severity.valueOf(value.toUpperCase()); }
    catch (IllegalArgumentException ex) { return Severity.MAJOR; }
  }
}
