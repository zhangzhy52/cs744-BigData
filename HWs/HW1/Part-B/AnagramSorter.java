package org.myorg;

import java.io.*;
import java.io.IOException;
import java.util.*;

import org.apache.hadoop.fs.Path;
import org.apache.hadoop.conf.*;
import org.apache.hadoop.io.*;
import org.apache.hadoop.mapred.*;
//import org.apache.hadoop.mapreduce.*;
import org.apache.hadoop.util.*;
import org.apache.commons.lang.StringUtils;
  
public class AnagramSorter {
  
  public static class DescendingKeyComparator extends WritableComparator {
    protected DescendingKeyComparator() {
      super(Text.class, true);
    }

    @SuppressWarnings("rawtypes")
    @Override
    public int compare(WritableComparable w1, WritableComparable w2) {
      IntWritable key1 = (IntWritable) w1;
      IntWritable key2 = (IntWritable) w2;          
      return -1 * key1.compareTo(key2);
    }
  }
  public static class Anagram {
    public static class Map extends MapReduceBase implements Mapper<LongWritable, Text, Text, Text> {
      private final static IntWritable one = new IntWritable(1);
      private Text word = new Text();
      private Text sorted = new Text();

      public void map(LongWritable key, Text value, OutputCollector<Text, Text> output, Reporter reporter) throws IOException {
        String line = value.toString();
        StringTokenizer tokenizer = new StringTokenizer(line);
        while (tokenizer.hasMoreTokens()) {
          word.set(tokenizer.nextToken());
          char[] chars = word.toString().toCharArray();
          Arrays.sort(chars);
          sorted.set(new String(chars));
          output.collect(sorted, word);
        }
      }
    }
    
    public static class Reduce  extends MapReduceBase implements Reducer<Text, Text, Text, Text> {
      public void reduce(Text key, Iterator<Text> values, OutputCollector<Text, Text> output, Reporter reporter) throws IOException {
        //int sum = 0;
        //while (values.hasNext()) {
        //  sum += values.next().get();
        //}
        //output.collect(key, new IntWritable(sum));
        //ArrayList<IntWritable> list = new ArrayList<IntWritable>();    
        StringBuilder strVal = new StringBuilder();
        while ( values.hasNext()) {
           
          strVal.append(values.next().toString());
          if(values.hasNext())
            strVal.append(",");
        }
        //output.collect(key, new MyArrayWritable(IntWritable.class, list.toArray(new IntWritable[list.size()]) ) );
        output.collect(key, new Text(strVal.toString()));
        //context.write(key, new MyArrayWritable(IntWritable.class, list.toArray(new IntWritable[list.size()])));
      }
    }
  };

  public static class MySorter {
    public static class Map extends MapReduceBase implements Mapper<LongWritable, Text, IntWritable, Text> {
      //private final static IntWritable one = new IntWritable(1);
      private Text word = new Text(); 
      //private Text sorted = new Text(); 

      public void map(LongWritable key, Text value, OutputCollector<IntWritable, Text> output, Reporter reporter) throws IOException {
        String line = value.toString();
        StringTokenizer tokenizer = new StringTokenizer(line);
        while (tokenizer.hasMoreTokens()) {
          word.set(tokenizer.nextToken());
          
          int count = StringUtils.countMatches(word.toString(),",");        
          output.collect(new IntWritable(100-count), word);
        }
      }
    }

    public static class Reduce extends MapReduceBase implements Reducer<IntWritable, Text, NullWritable, Text> {
      public void reduce(IntWritable key, Iterator<Text> values, OutputCollector<NullWritable, Text> output, Reporter reporter) throws IOException {
        while ( values.hasNext()) {
          output.collect(NullWritable.get(), values.next());
        }
        //output.collect(NullWritable.get(), values);
      }
    } 
  };

  public static void main(String[] args) throws Exception {
    //Configuration conf = getConf();
    //Job job = new Job(conf, "AnagramSorter");
    
    JobConf job = new JobConf(AnagramSorter.class);
    job.setJobName("AnagramSorter_Anagram");

    job.setMapOutputKeyClass(Text.class);
    job.setMapOutputValueClass(Text.class);

    job.setOutputKeyClass(Text.class);
    job.setOutputValueClass(Text.class);

    job.setMapperClass(Anagram.Map.class);
    //conf.setCombinerClass(Reduce.class);
    job.setReducerClass(Anagram.Reduce.class);

    // Set Output and Input Parameters
    //job.setMapOutputKeyClass(Text.class);
    //job.setMapOutputValueClass(IntWritable.class);

    //job.setOutputKeyClass(Text.class);
    //job.setOutputValueClass(MyArrayWritable.class);
    
    // set IO value
    job.setInputFormat(TextInputFormat.class);
    job.setOutputFormat(TextOutputFormat.class);

    FileInputFormat.setInputPaths(job, new Path(args[0]));
    FileOutputFormat.setOutputPath(job, new Path("inter_dir/output"));

    JobClient.runJob(job);
    
    //job.waitForCompletion(true);
    ///////////////////////////////////////////////////////////////
    // The sorter part
            
    JobConf job2 = new JobConf(AnagramSorter.class);
    job2.setJobName("AnagramSorter_sort");

    job2.setMapOutputKeyClass(IntWritable.class);
    job2.setMapOutputValueClass(Text.class);

    job2.setOutputKeyClass(NullWritable.class);
    job2.setOutputValueClass(Text.class);
    
    //job2.setOutputKeyComparatorClass(DescendingKeyComparator.class);
    job2.setMapperClass(MySorter.Map.class);
    //conf.setCombinerClass(Reduce.class);
    job2.setReducerClass(MySorter.Reduce.class);

    // Set Output and Input Parameters
    //job.setMapOutputKeyClass(Text.class);
    //job.setMapOutputValueClass(IntWritable.class);

    //job.setOutputKeyClass(Text.class);
    //job.setOutputValueClass(MyArrayWritable.class);

    // set IO value
    job2.setInputFormat(TextInputFormat.class);
    job2.setOutputFormat(TextOutputFormat.class);

    FileInputFormat.setInputPaths(job2, new Path("inter_dir/output"));
    FileOutputFormat.setOutputPath(job2, new Path(args[1]));

    JobClient.runJob(job2);
    
  }
}

class MyArrayWritable extends ArrayWritable{

  public MyArrayWritable(Class<? extends Writable> valueClass, Writable[] values) {
    super(valueClass, values);
  }
  public MyArrayWritable(Class<? extends Writable> valueClass) {
    super(valueClass);
  }

  @Override
  public IntWritable[] get() {
    return (IntWritable[]) super.get();
  }

  @Override
  public void write(DataOutput arg0) throws IOException {
    System.out.println("write method called");
    super.write(arg0);
  }
  
  @Override
  public String toString() {
    return Arrays.toString(get());
  }

}
